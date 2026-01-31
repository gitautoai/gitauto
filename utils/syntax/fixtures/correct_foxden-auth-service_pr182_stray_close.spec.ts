import { createMocks } from 'node-mocks-http';

import { logout } from '../../../src/routes';

const RedirectTo = 'https://www.foxquilt.com/';

describe('Logout route', () => {
  let oldEnv: unknown;
  let log: any;

  beforeAll(() => {
    oldEnv = Object.assign({}, process.env);
    process.env.FDAUTH_LOGOUT_URL = 'https://www.foxquilt.com/';
  });

  afterAll(() => {
    Object.assign(process.env, oldEnv);
  });

  beforeEach(() => {
    log = {
      debug: jest.fn(),
      error: jest.fn(),
    };
  });

  describe('With redirectTo parameter', () => {
    it('Will logout user and invoke next handler', () => {
      const logoutMock = jest.fn().mockImplementation((callback) => callback());
      const nextHandler = jest.fn();
      const { req, res } = createMocks({
        log,
        logout: logoutMock,
        query: {
          redirectTo: RedirectTo,
        },
      });

      logout(req, res, nextHandler);

      expect(log.debug).toHaveBeenCalledWith('Attempting to end session', {
        sessionId: req.sessionID,
        user: undefined,
      });
      expect(logoutMock).toBeCalled();
      expect(nextHandler).toBeCalledWith();
      expect(res._isEndCalled()).toEqual(false);
      expect(req.query.redirectTo).toEqual(RedirectTo);
    });

    it('Will log error and invoke next handler without error if logout fails', () => {
      const error = new Error('Uh oh!');
      const logoutMock = jest
        .fn()
        .mockImplementation((callback) => callback(error));
      const nextHandler = jest.fn();
      const { req, res } = createMocks({
        log,
        logout: logoutMock,
        query: {
          redirectTo: RedirectTo,
        },
      });

      logout(req, res, nextHandler);

      expect(log.debug).toHaveBeenCalledWith('Attempting to end session', {
        sessionId: req.sessionID,
        user: undefined,
      });
      expect(log.error).toHaveBeenCalledWith(error);
      expect(logoutMock).toBeCalled();
      expect(nextHandler).toBeCalledWith();
      expect(res._isEndCalled()).toEqual(false);
      expect(req.query.redirectTo).toEqual(RedirectTo);
    });

    it('Will redirect to indicated URL if an error occurs and failureRedirectTo parameter is present', () => {
      const failureRedirectTo = 'https://otherwebsite.com/uh-oh';
      const error = new Error('Uh oh!');
      const logoutMock = jest
        .fn()
        .mockImplementation((callback) => callback(error));
      const nextHandler = jest.fn();
      const { req, res } = createMocks({
        log,
        logout: logoutMock,
        query: {
          redirectTo: RedirectTo,
          failureRedirectTo,
        },
      });

      logout(req, res, nextHandler);

      expect(log.debug).toHaveBeenCalledWith('Attempting to end session', {
        sessionId: req.sessionID,
        user: undefined,
      });
      expect(log.error).toHaveBeenCalledWith(error);
      expect(logoutMock).toBeCalled();
      expect(nextHandler).toBeCalledWith();
      expect(res._isEndCalled()).toEqual(false);
      expect(req.query.redirectTo).toEqual(failureRedirectTo);
    });
  });

  describe('Without redirectTo parameter', () => {
    it('Will redirect to indicated logout url always', () => {
      const logoutUrl = process.env.FDAUTH_LOGOUT_URL;
      const logoutMock = jest.fn().mockImplementation((callback) => callback());
      const nextHandler = jest.fn();
      const { req, res } = createMocks({
        log,
        logout: logoutMock,
      });

      logout(req, res, nextHandler);

      expect(log.debug).toHaveBeenNthCalledWith(
        1,
        'Attempting to end session',
        {
          sessionId: req.sessionID,
          user: undefined,
        },
      );
      expect(log.debug).toHaveBeenNthCalledWith(
        2,
        'Session successfully closed.',
        {
          sessionId: req.sessionID,
          user: undefined,
        },
      );
      expect(logoutMock).toBeCalled();
      expect(nextHandler).toBeCalledWith();
      expect(res._isEndCalled()).toEqual(false);
      expect(req.query.redirectTo).toEqual(logoutUrl);
    });

    it('Will pass error to next handler if logout fails', () => {
      const error = new Error('Uh oh! Logout failed');
      const logoutMock = jest
        .fn()
        .mockImplementation((callback) => callback(error));
      const nextHandler = jest.fn();
      const { req, res } = createMocks({
        log,
        logout: logoutMock,
      });

      logout(req, res, nextHandler);

      expect(log.debug).toHaveBeenCalledWith('Attempting to end session', {
        sessionId: req.sessionID,
        user: undefined,
      });
      expect(log.error).toHaveBeenCalledWith(error);
      expect(logoutMock).toBeCalled();
      expect(nextHandler).toBeCalledWith(error);
      expect(res._isEndCalled()).toEqual(false);
    });

    it('Will redirect to indicated URL if an error occurs and failureRedirectTo parameter is present', () => {
      const failureRedirectTo = 'https://otherwebsite.com/uh-oh';
      const error = new Error('Uh oh!');
      const logoutMock = jest
        .fn()
        .mockImplementation((callback) => callback(error));
      const nextHandler = jest.fn();
      const { req, res } = createMocks({
        log,
        logout: logoutMock,
        query: {
          failureRedirectTo,
        },
      });

      logout(req, res, nextHandler);

      expect(log.debug).toHaveBeenCalledWith('Attempting to end session', {
        sessionId: req.sessionID,
        user: undefined,
      });
      expect(log.error).toHaveBeenCalledWith(error);
      expect(logoutMock).toBeCalled();
      expect(nextHandler).toBeCalledWith();
      expect(res._isEndCalled()).toEqual(false);
      expect(req.query.redirectTo).toEqual(failureRedirectTo);
    });
  });

  describe('With user session', () => {
    it('Will include user email in session info when logging out', () => {
      const user = { email: 'test@example.com' };
      const logoutMock = jest.fn().mockImplementation((callback) => callback());
      const nextHandler = jest.fn();
      const { req, res } = createMocks({
        log,
        logout: logoutMock,
        user,
        query: {
          redirectTo: RedirectTo,
        },
      });

      logout(req, res, nextHandler);

      expect(log.debug).toHaveBeenCalledWith('Attempting to end session', {
        sessionId: req.sessionID,
        user: 'test@example.com',
      });
      expect(log.debug).toHaveBeenCalledWith('Session successfully closed.', {
        sessionId: req.sessionID,
        user: 'test@example.com',
      });
      expect(logoutMock).toBeCalled();
      expect(nextHandler).toBeCalledWith();
    });
  });
});
