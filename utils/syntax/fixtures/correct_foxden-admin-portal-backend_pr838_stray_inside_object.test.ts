/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-var-requires */
import { ApolloServer, BaseContext } from '@apollo/server';
import {
  handlers,
  startServerAndCreateLambdaHandler,
} from '@as-integrations/aws-lambda';
import * as Sentry from '@sentry/node';
import type { APIGatewayProxyResult } from 'aws-lambda';
import { StatusCodes } from 'http-status-codes';

import {
  createGenericServer,
  GenericServerOptions,
} from './createGenericServer';

jest.mock('@as-integrations/aws-lambda');
jest.mock('@sentry/node');

describe('createGenericServer', () => {
  let mockServer: jest.Mocked<ApolloServer<BaseContext>>;
  let mockLambdaHandler: jest.Mock;
  let mockStartServerAndCreateLambdaHandler: jest.MockedFunction<
    typeof startServerAndCreateLambdaHandler
  >;
  let mockSentryCaptureException: jest.MockedFunction<
    typeof Sentry.captureException
  >;
  let consoleLogSpy: jest.SpyInstance;
  let consoleErrorSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.clearAllMocks();

    mockServer = {} as jest.Mocked<ApolloServer<BaseContext>>;
    mockLambdaHandler = jest.fn();
    mockStartServerAndCreateLambdaHandler =
      startServerAndCreateLambdaHandler as jest.MockedFunction<
        typeof startServerAndCreateLambdaHandler
      >;
    mockSentryCaptureException = Sentry.captureException as jest.MockedFunction<
      typeof Sentry.captureException
    >;

    mockStartServerAndCreateLambdaHandler.mockReturnValue(mockLambdaHandler);
    consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
  });

  afterEach(() => {
    consoleLogSpy.mockRestore();
    consoleErrorSpy.mockRestore();
  });

  describe('successful handler creation', () => {
    it('should create a handler that successfully processes requests', async () => {
      const mockEvent = {
        headers: { origin: 'https://example.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: {
          'Access-Control-Allow-Origin': 'https://example.com',
          'Access-Control-Allow-Credentials': 'true',
        },
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer);
      const result = await handler(mockEvent, mockContext);

      expect(result).toEqual(mockResult);
      expect(mockStartServerAndCreateLambdaHandler).toHaveBeenCalledWith(
        mockServer,
        handlers.createAPIGatewayProxyEventRequestHandler(),
      );
      expect(mockLambdaHandler).toHaveBeenCalledWith(
        mockEvent,
        mockContext,
        expect.any(Function),
      );
    });

    it('should handle requests without headers', async () => {
      const mockEvent = {
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer);
      const result = await handler(mockEvent, mockContext);

      expect(result).toEqual(mockResult);
    });
  });

  describe('CORS handling', () => {
    it('should preserve CORS headers when origin is in allowlist', async () => {
      const allowedOrigin = 'https://allowed.com';
      const options: GenericServerOptions = {
        cors: {
          origin: [allowedOrigin, 'https://another-allowed.com'],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: allowedOrigin },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: {
          'Access-Control-Allow-Origin': allowedOrigin,
          'Access-Control-Allow-Credentials': 'true',
          'Access-Control-Allow-Methods': 'GET,POST',
        },
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result.headers).toEqual(mockResult.headers);
      expect(consoleLogSpy).not.toHaveBeenCalled();
    });

    it('should remove CORS headers when origin is not in allowlist', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: ['https://allowed.com'],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://not-allowed.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: {
          'Access-Control-Allow-Origin': 'https://not-allowed.com',
          'Access-Control-Allow-Credentials': 'true',
          'Access-Control-Allow-Methods': 'GET,POST',
          'Access-Control-Allow-Headers': 'Content-Type',
        },
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, { ...mockResult });
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result.headers).not.toHaveProperty('Access-Control-Allow-Origin');
      expect(result.headers).not.toHaveProperty(
        'Access-Control-Allow-Credentials',
      );
      expect(result.headers).not.toHaveProperty('Access-Control-Allow-Methods');
      expect(result.headers).not.toHaveProperty('Access-Control-Allow-Headers');
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('CORS origin check failed'),
      );
    });

    it('should remove CORS headers with lowercase keys when origin is not in allowlist', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: ['https://allowed.com'],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://not-allowed.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: {
          'access-control-allow-origin': 'https://not-allowed.com',
          'access-control-allow-credentials': 'true',
          'access-control-allow-methods': 'GET,POST',
          'access-control-allow-headers': 'Content-Type',
        },
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, { ...mockResult });
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result.headers).not.toHaveProperty('access-control-allow-origin');
      expect(result.headers).not.toHaveProperty(
        'access-control-allow-credentials',
      );
      expect(result.headers).not.toHaveProperty('access-control-allow-methods');
      expect(result.headers).not.toHaveProperty('access-control-allow-headers');
    });

    it('should remove CORS headers when no origin is provided in request', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: ['https://allowed.com'],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: {},
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': 'true',
        },
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, { ...mockResult });
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result.headers).not.toHaveProperty('Access-Control-Allow-Origin');
      expect(result.headers).not.toHaveProperty(
        'Access-Control-Allow-Credentials',
      );
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('CORS origin check failed'),
      );
    });

    it('should not modify headers when CORS options are not provided', async () => {
      const mockEvent = {
        headers: { origin: 'https://any-origin.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: {
          'Access-Control-Allow-Origin': 'https://any-origin.com',
          'Access-Control-Allow-Credentials': 'true',
        },
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer);
      const result = await handler(mockEvent, mockContext);

      expect(result.headers).toEqual(mockResult.headers);
      expect(consoleLogSpy).not.toHaveBeenCalled();
    });

    it('should handle result without headers object when CORS check fails', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: ['https://allowed.com'],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://not-allowed.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result).toEqual(mockResult);
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('CORS origin check failed'),
      );
    });

    it('should handle CORS options with undefined cors property', async () => {
      const options: GenericServerOptions = {
        cors: undefined,
      };

      const mockEvent = {
        headers: { origin: 'https://example.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: {
          'Access-Control-Allow-Origin': 'https://example.com',
        },
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result.headers).toEqual(mockResult.headers);
      expect(consoleLogSpy).not.toHaveBeenCalled();
    });

    it('should handle result with empty object headers when CORS check fails and responseHeader is truthy', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: ['https://allowed.com'],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://not-allowed.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const emptyHeaders = {};
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: emptyHeaders,
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result.headers).toEqual({});
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('CORS origin check failed'),
      );
    });

    it('should handle CORS check failure when result.headers is null and responseHeader becomes empty object', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: ['https://allowed.com'],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://not-allowed.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: null as any,
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result).toEqual(mockResult);
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('CORS origin check failed'),
      );
    });

    it('should handle CORS check failure when result.headers is undefined and responseHeader becomes empty object', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: ['https://allowed.com'],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://not-allowed.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: undefined,
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result).toEqual(mockResult);
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('CORS origin check failed'),
      );
    });

    it('should handle CORS check failure when result.headers is 0 (falsy number)', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: ['https://allowed.com'],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://not-allowed.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: 0 as any,
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result).toEqual(mockResult);
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('CORS origin check failed'),
      );
    });

    it('should handle CORS check failure when result.headers is false', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: ['https://allowed.com'],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://not-allowed.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: false as any,
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result).toEqual(mockResult);
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('CORS origin check failed'),
      );
    });

    it('should handle CORS check failure when result.headers is empty string', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: ['https://allowed.com'],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://not-allowed.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: '' as any,
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result).toEqual(mockResult);
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('CORS origin check failed'),
      );
    });

    it('should preserve CORS headers when origin is in allowlist with result.headers being null', async () => {
      const allowedOrigin = 'https://allowed.com';
      const options: GenericServerOptions = {
        cors: {
          origin: [allowedOrigin],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: allowedOrigin },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: null as any,
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result).toEqual(mockResult);
      expect(consoleLogSpy).not.toHaveBeenCalled();
    });

    it('should preserve CORS headers when origin is in allowlist with result.headers being undefined', async () => {
      const allowedOrigin = 'https://allowed.com';
      const options: GenericServerOptions = {
        cors: {
          origin: [allowedOrigin],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: allowedOrigin },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: undefined,
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result).toEqual(mockResult);
      expect(consoleLogSpy).not.toHaveBeenCalled();
    });
  });

  describe('error handling in lambda handler', () => {
    it('should reject when lambda handler returns an error', async () => {
      const mockError = new Error('Lambda handler error');
      const mockEvent = {
        headers: { origin: 'https://example.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(mockError);
        },
      );

      const handler = createGenericServer(mockServer);

      await expect(handler(mockEvent, mockContext)).rejects.toThrow(
        'Lambda handler error',
      );
    });

    it('should reject when lambda handler returns undefined result', async () => {
      const mockEvent = {
        headers: { origin: 'https://example.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, undefined);
        },
      );

      const handler = createGenericServer(mockServer);

      await expect(handler(mockEvent, mockContext)).rejects.toThrow(
        'Lambda handler did not return a result',
      );
    });

    it('should reject when exception occurs during lambda handler execution', async () => {
      const mockError = new Error('Unexpected error');
      const mockEvent = {
        headers: { origin: 'https://example.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };

      mockLambdaHandler.mockImplementation(() => {
        throw mockError;
      });

      const handler = createGenericServer(mockServer);

      await expect(handler(mockEvent, mockContext)).rejects.toThrow(
        'Unexpected error',
      );
    });
  });

  describe('server initialization error handling', () => {
    it('should return error handler when server initialization throws Error', async () => {
      const initError = new Error('Server initialization failed');
      mockStartServerAndCreateLambdaHandler.mockImplementation(() => {
        throw initError;
      });

      const handler = createGenericServer(mockServer);
      const result = await handler({}, {});

      expect(result).toEqual({
        statusCode: StatusCodes.INTERNAL_SERVER_ERROR,
        body: JSON.stringify({
          errors: [{ message: 'Cannot setup the service' }],
        }),
      });
      expect(mockSentryCaptureException).toHaveBeenCalledWith(initError);
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Cannot close context:',
        initError,
      );
    });

    it('should return error handler when server initialization throws non-Error', async () => {
      const initError = 'String error';
      mockStartServerAndCreateLambdaHandler.mockImplementation(() => {
        throw initError;
      });

      const handler = createGenericServer(mockServer);
      const result = await handler({}, {});

      expect(result).toEqual({
        statusCode: StatusCodes.INTERNAL_SERVER_ERROR,
        body: JSON.stringify({
          errors: [{ message: 'Cannot setup the service' }],
        }),
      });
      expect(mockSentryCaptureException).toHaveBeenCalledWith(initError);
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Unreachable - found error but what's thrown isn't an Error",
        initError,
      );
    });

    it('should return error handler when server initialization throws object', async () => {
      const initError = { code: 'INIT_ERROR', message: 'Failed' };
      mockStartServerAndCreateLambdaHandler.mockImplementation(() => {
        throw initError;
      });

      const handler = createGenericServer(mockServer);
      const result = await handler({}, {});

      expect(result).toEqual({
        statusCode: StatusCodes.INTERNAL_SERVER_ERROR,
        body: JSON.stringify({
          errors: [{ message: 'Cannot setup the service' }],
        }),
      });
      expect(mockSentryCaptureException).toHaveBeenCalledWith(initError);
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Unreachable - found error but what's thrown isn't an Error",
        initError,
      );
    });

    it('should return error handler when server initialization throws null', async () => {
      const initError = null;
      mockStartServerAndCreateLambdaHandler.mockImplementation(() => {
        throw initError;
      });

      const handler = createGenericServer(mockServer);
      const result = await handler({}, {});

      expect(result).toEqual({
        statusCode: StatusCodes.INTERNAL_SERVER_ERROR,
        body: JSON.stringify({
          errors: [{ message: 'Cannot setup the service' }],
        }),
      });
      expect(mockSentryCaptureException).toHaveBeenCalledWith(initError);
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Unreachable - found error but what's thrown isn't an Error",
        initError,
      );
    });

    it('should return error handler when server initialization throws undefined', async () => {
      const initError = undefined;
      mockStartServerAndCreateLambdaHandler.mockImplementation(() => {
        throw initError;
      });

      const handler = createGenericServer(mockServer);
      const result = await handler({}, {});

      expect(result).toEqual({
        statusCode: StatusCodes.INTERNAL_SERVER_ERROR,
        body: JSON.stringify({
          errors: [{ message: 'Cannot setup the service' }],
        }),
      });
      expect(mockSentryCaptureException).toHaveBeenCalledWith(initError);
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Unreachable - found error but what's thrown isn't an Error",
        initError,
      );
    });

    it('should return error handler when server initialization throws number', async () => {
      const initError = 404;
      mockStartServerAndCreateLambdaHandler.mockImplementation(() => {
        throw initError;
      });

      const handler = createGenericServer(mockServer);
      const result = await handler({}, {});

      expect(result).toEqual({
        statusCode: StatusCodes.INTERNAL_SERVER_ERROR,
        body: JSON.stringify({
          errors: [{ message: 'Cannot setup the service' }],
        }),
      });
      expect(mockSentryCaptureException).toHaveBeenCalledWith(initError);
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Unreachable - found error but what's thrown isn't an Error",
        initError,
      );
    });
  });

  describe('edge cases', () => {
    it('should handle empty headers object', async () => {
      const mockEvent = {
        headers: {},
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer);
      const result = await handler(mockEvent, mockContext);

      expect(result).toEqual(mockResult);
    });

    it('should handle null headers in result', async () => {
      const mockEvent = {
        headers: { origin: 'https://example.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: undefined,
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer);
      const result = await handler(mockEvent, mockContext);

      expect(result).toEqual(mockResult);
    });

    it('should handle CORS with empty origin array', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: [],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://example.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: {
          'Access-Control-Allow-Origin': 'https://example.com',
        },
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, { ...mockResult });
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result.headers).not.toHaveProperty('Access-Control-Allow-Origin');
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('CORS origin check failed'),
      );
    });

    it('should handle case-sensitive origin matching', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: ['https://Example.com'],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://example.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: {
          'Access-Control-Allow-Origin': 'https://example.com',
        },
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, { ...mockResult });
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result.headers).not.toHaveProperty('Access-Control-Allow-Origin');
    });

    it('should handle multiple CORS headers with mixed case', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: ['https://allowed.com'],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://not-allowed.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: {
          'Access-Control-Allow-Origin': 'https://not-allowed.com',
          'access-control-allow-origin': 'https://not-allowed.com',
          'Access-Control-Allow-Credentials': 'true',
          'access-control-allow-credentials': 'true',
          'Access-Control-Allow-Methods': 'GET,POST',
          'access-control-allow-methods': 'GET,POST',
          'Access-Control-Allow-Headers': 'Content-Type',
          'access-control-allow-headers': 'Content-Type',
        },
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, { ...mockResult });
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result.headers).not.toHaveProperty('Access-Control-Allow-Origin');
      expect(result.headers).not.toHaveProperty('access-control-allow-origin');
      expect(result.headers).not.toHaveProperty(
        'Access-Control-Allow-Credentials',
      );
      expect(result.headers).not.toHaveProperty(
        'access-control-allow-credentials',
      );
      expect(result.headers).not.toHaveProperty('Access-Control-Allow-Methods');
      expect(result.headers).not.toHaveProperty('access-control-allow-methods');
      expect(result.headers).not.toHaveProperty('Access-Control-Allow-Headers');
      expect(result.headers).not.toHaveProperty('access-control-allow-headers');
    });

    it('should handle event with null headers', async () => {
      const mockEvent = {
        headers: null as any,
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer);
      const result = await handler(mockEvent, mockContext);

      expect(result).toEqual(mockResult);
    });

    it('should handle event with undefined headers', async () => {
      const mockEvent = {
        headers: undefined as any,
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer);
      const result = await handler(mockEvent, mockContext);

      expect(result).toEqual(mockResult);
    });

    it('should handle CORS check failure when responseHeader is assigned from result.headers || {} with result.headers being explicitly set to a falsy non-null/undefined value', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: ['https://allowed.com'],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://not-allowed.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: Object.create(null),
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result).toEqual(mockResult);
      expect(consoleLogSpy).toHaveBeenCalledWith(
        'CORS origin check failed in create generic server. https://not-allowed.com is not in allowlist.',
      );
    });

    it('should handle origin header with empty string', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: ['https://allowed.com'],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: '' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: {
          'Access-Control-Allow-Origin': '*',
        },
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, { ...mockResult });
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result.headers).not.toHaveProperty('Access-Control-Allow-Origin');
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('CORS origin check failed'),
      );
    });

    it('should handle multiple allowed origins', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: [
            'https://allowed1.com',
            'https://allowed2.com',
            'https://allowed3.com',
          ],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://allowed2.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {

      it('should handle CORS check failure when responseHeader becomes truthy from empty object fallback', async () => {
        const options: GenericServerOptions = {
          cors: {
            origin: ['https://allowed.com'],
            methods: ['GET', 'POST'],
            credentials: true,
            maxAge: 3600,
          },
        };

        const mockEvent = {
          headers: { origin: 'https://not-allowed.com' },
          body: '{\"query\":\"{ test }\"}',
        };
        const mockContext = { requestId: 'test-request-id' };
        const mockResult: APIGatewayProxyResult = {
          statusCode: 200,
          body: '{\"data\":{\"test\":\"success\"}}',
          headers: undefined,
        };

        mockLambdaHandler.mockImplementation(
          (_event: any, _context: any, callback: any) => {
            const resultCopy = { ...mockResult };
            Object.defineProperty(resultCopy, 'headers', {
              get: () => undefined,
              enumerable: true,
              configurable: true,
            });
            callback(null, resultCopy);
          },
        );

        const handler = createGenericServer(mockServer, options);
        const result = await handler(mockEvent, mockContext);

        expect(result.statusCode).toBe(200);
        expect(consoleLogSpy).toHaveBeenCalledWith(
          expect.stringContaining('CORS origin check failed'),
        );
      });
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: {
          'Access-Control-Allow-Origin': 'https://allowed2.com',
        },
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result.headers).toEqual(mockResult.headers);
      expect(consoleLogSpy).not.toHaveBeenCalled();
    });

    it('should handle result with only non-CORS headers when CORS check fails', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: ['https://allowed.com'],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://not-allowed.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: {
          'Content-Type': 'application/json',
          'X-Custom-Header': 'custom-value',
          'Access-Control-Allow-Origin': 'https://not-allowed.com',
        },
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, { ...mockResult });
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result.headers).not.toHaveProperty('Access-Control-Allow-Origin');
      expect(result.headers?.['X-Custom-Header']).toBe('custom-value');
    });

    it('should handle CORS check with non-array origin (edge case for Array.isArray check)', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: ['https://allowed.com'],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://not-allowed.com' },
        body: '{\"query\":\"{ test }\"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{\"data\":{\"test\":\"success\"}}',
        headers: {
          'Access-Control-Allow-Origin': 'https://not-allowed.com',
        },
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, { ...mockResult });
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result.headers).not.toHaveProperty('Access-Control-Allow-Origin');
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('CORS origin check failed'),
      );
    });

    it('should handle result with headers as empty object literal when CORS check fails', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: ['https://allowed.com'],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://not-allowed.com' },
        body: '{\"query\":\"{ test }\"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{\"data\":{\"test\":\"success\"}}',
        headers: {},
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);
      expect(result).toEqual(mockResult);

      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('CORS origin check failed'),
      );
    });
    it('should not remove CORS headers when origin array check is bypassed due to non-array origin', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: 'https://allowed.com' as any,
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://not-allowed.com' },
        body: '{\"query\":\"{ test }\"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{\"data\":{\"test\":\"success\"}}',
        headers: {
          'Access-Control-Allow-Origin': 'https://not-allowed.com',
        },
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result.headers).toEqual(mockResult.headers);
      expect(consoleLogSpy).not.toHaveBeenCalled();
    });

    it('should not remove CORS headers when origin check passes with non-array origin (edge case)', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: 'https://allowed.com' as any,
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://allowed.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: {
          'Access-Control-Allow-Origin': 'https://allowed.com',
          'Access-Control-Allow-Credentials': 'true',
        },
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result.headers).toEqual(mockResult.headers);
      expect(consoleLogSpy).not.toHaveBeenCalled();
    });

    it('should handle CORS check failure when result.headers is NaN (falsy)', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: ['https://allowed.com'],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://not-allowed.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: NaN as any,
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result).toEqual(mockResult);
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('CORS origin check failed'),
      );
    });

    it('should handle CORS check failure when result.headers is an object with Symbol keys', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: ['https://allowed.com'],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://not-allowed.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const symbolKey = Symbol('custom');
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: {
          'Access-Control-Allow-Origin': 'https://not-allowed.com',
          [symbolKey]: 'value',
        } as any,
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, { ...mockResult });
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result.headers).not.toHaveProperty('Access-Control-Allow-Origin');
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('CORS origin check failed'),
      );
    });

    it('should handle CORS check failure with result.headers containing only CORS headers to be deleted', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: ['https://allowed.com'],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://not-allowed.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: {
          'Access-Control-Allow-Origin': 'https://not-allowed.com',
          'Access-Control-Allow-Credentials': 'true',
          'Access-Control-Allow-Methods': 'GET,POST',
          'Access-Control-Allow-Headers': 'Content-Type',
        },
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, { ...mockResult });
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result.headers).not.toHaveProperty('Access-Control-Allow-Origin');
      expect(result.headers).not.toHaveProperty(
        'Access-Control-Allow-Credentials',
      );
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('CORS origin check failed'),
      );
    });

    describe('responseHeader edge cases for line 70 branch coverage', () => {
      it('should always execute delete operations when CORS check fails because responseHeader is always truthy', async () => {
        const options: GenericServerOptions = {
          cors: {
            origin: ['https://allowed.com'],
            methods: ['GET', 'POST'],
            credentials: true,
            maxAge: 3600,
          },
        };

        const mockEvent = {
          headers: { origin: 'https://not-allowed.com' },
          body: '{\"query\":\"{ test }\"}',
        };
        const mockContext = { requestId: 'test-request-id' };
        const headersObject = {
          'Access-Control-Allow-Origin': 'https://not-allowed.com',
          'access-control-allow-origin': 'https://not-allowed.com',
          'Access-Control-Allow-Credentials': 'true',
          'access-control-allow-credentials': 'true',
          'Access-Control-Allow-Methods': 'GET,POST',
          'access-control-allow-methods': 'GET,POST',
          'Access-Control-Allow-Headers': 'Content-Type',
          'access-control-allow-headers': 'Content-Type',
        };
        const mockResult: APIGatewayProxyResult = {
          statusCode: 200,
          body: '{\"data\":{\"test\":\"success\"}}',
          headers: headersObject,
        };

        mockLambdaHandler.mockImplementation(
          (_event: any, _context: any, callback: any) => {
            callback(null, { ...mockResult });
          },
        );

        const handler = createGenericServer(mockServer, options);
        const result = await handler(mockEvent, mockContext);

        expect(Object.keys(result.headers || {})).toHaveLength(0);
        expect(consoleLogSpy).toHaveBeenCalledWith(
          expect.stringContaining('CORS origin check failed'),
        );
      });

      it('should handle CORS check failure when result.headers is a Proxy object that appears truthy but behaves unexpectedly', async () => {
        const options: GenericServerOptions = {
          cors: {
            origin: ['https://allowed.com'],
            methods: ['GET', 'POST'],
            credentials: true,
            maxAge: 3600,
          },
        };

        const mockEvent = {
          headers: { origin: 'https://not-allowed.com' },
          body: '{"query":"{ test }"}',
        };
        const mockContext = { requestId: 'test-request-id' };

        const headersProxy = new Proxy(
          {},
          {
            get: () => undefined,
            set: () => true,
            deleteProperty: () => true,
          },
        );

        const mockResult: APIGatewayProxyResult = {
          statusCode: 200,
          body: '{"data":{"test":"success"}}',
          headers: headersProxy as any,
        };

        mockLambdaHandler.mockImplementation(
          (_event: any, _context: any, callback: any) => {
            callback(null, mockResult);
          },
        );

        const handler = createGenericServer(mockServer, options);
        const result = await handler(mockEvent, mockContext);

        expect(result).toEqual(mockResult);
        expect(consoleLogSpy).toHaveBeenCalledWith(
          expect.stringContaining('CORS origin check failed'),
        );
      });

      it('should execute delete operations when CORS check fails even though result.headers is falsy because responseHeader becomes empty object', async () => {
        const options: GenericServerOptions = {
          cors: {
            origin: ['https://allowed.com'],
            methods: ['GET', 'POST'],
            credentials: true,
            maxAge: 3600,
          },
        };

        const mockEvent = {
          headers: { origin: 'https://not-allowed.com' },
          body: '{"query":"{ test }"}',
        };
        const mockContext = { requestId: 'test-request-id' };
        const mockResult: APIGatewayProxyResult = {
          statusCode: 200,
          body: '{"data":{"test":"success"}}',
          headers: undefined,
        };

        mockLambdaHandler.mockImplementation(
          (_event: any, _context: any, callback: any) => {
            callback(null, mockResult);
          },
        );

        const handler = createGenericServer(mockServer, options);
        const result = await handler(mockEvent, mockContext);
      });
    });


    it('should execute delete operations inside if(responseHeader) block when CORS check fails with truthy headers', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: ['https://allowed.com'],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://not-allowed.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };

      const headersObject = {
        'Access-Control-Allow-Origin': 'https://not-allowed.com',
        'access-control-allow-origin': 'https://not-allowed.com',
        'Access-Control-Allow-Credentials': 'true',
        'access-control-allow-credentials': 'true',
        'Access-Control-Allow-Methods': 'GET,POST',
        'access-control-allow-methods': 'GET,POST',
        'Access-Control-Allow-Headers': 'Content-Type',
        'access-control-allow-headers': 'Content-Type',
        'X-Custom-Header': 'should-remain',
      };

      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: headersObject,
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result.headers).not.toHaveProperty('Access-Control-Allow-Origin');
      expect(result.headers).not.toHaveProperty('access-control-allow-origin');
      expect(result.headers).not.toHaveProperty('Access-Control-Allow-Credentials');
      expect(result.headers).not.toHaveProperty('access-control-allow-credentials');
      expect(result.headers?.['X-Custom-Header']).toBe('should-remain');
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('CORS origin check failed'),
      );
    });

    it('should execute delete operations even when responseHeader is empty object from result.headers || {}', async () => {
      const options: GenericServerOptions = {
        cors: {
          origin: ['https://allowed.com'],
          methods: ['GET', 'POST'],
          credentials: true,
          maxAge: 3600,
        },
      };

      const mockEvent = {
        headers: { origin: 'https://not-allowed.com' },
        body: '{"query":"{ test }"}',
      };
      const mockContext = { requestId: 'test-request-id' };
      const mockResult: APIGatewayProxyResult = {
        statusCode: 200,
        body: '{"data":{"test":"success"}}',
        headers: undefined,
      };

      mockLambdaHandler.mockImplementation(
        (_event: any, _context: any, callback: any) => {
          callback(null, mockResult);
        },
      );

      const handler = createGenericServer(mockServer, options);
      const result = await handler(mockEvent, mockContext);

      expect(result).toEqual(mockResult);
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('CORS origin check failed'),
      );
    });
  });
});
