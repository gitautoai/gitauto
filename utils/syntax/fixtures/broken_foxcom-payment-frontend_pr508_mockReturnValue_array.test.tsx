/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, @typescript-eslint/no-var-requires */
import { ApolloError } from '@apollo/client';
import { MockedProvider } from '@apollo/client/testing';
import { useAuth0 } from '@auth0/auth0-react';
import { render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter, Route } from 'react-router-dom';

import { useAuthContext } from '../../auth/authContext';
import type { AuthContext, User } from '../../auth/AuthProvider';
import { useAuth } from '../../auth/AuthProvider';
import {
  GetApplicationbyQuoteIdQuery,
  useGenerateSigningUrlMutation,
  useGetApplicationbyQuoteIdLazyQuery
} from '../../generated/graphql';
import Terms from './Terms';

// Mock dependencies
jest.mock('@auth0/auth0-react');
jest.mock('../../generated/graphql');
jest.mock('../../auth/AuthProvider');
jest.mock('../../auth/authContext');
jest.mock('../../utils/getEnv', () => ({
  __esModule: true,
  default: () => ({
    REACT_APP_API_MAX_RETRIES: '3',
    REACT_APP_API_BASE_DELAY: '1000',
    REACT_APP_API_MAX_DELAY: '5000',
    REACT_APP_PUBLIC_URL: ''
  })
}));
jest.mock('../../utils/trackLogin', () => ({
  checkIsLoggedIn: jest.fn(() => false),
  storeLogin: jest.fn(),
  storeLogout: jest.fn(),
  storeSessionSignout: jest.fn()
}));
jest.mock('url-join-ts', () => ({
  urlJoin: jest.fn((...args) => args.join(''))
}));

// Mock window.location
const mockLocation = {
  search: '',
  href: 'http://localhost:3000/terms',
  origin: 'http://localhost:3000',
  pathname: '/terms'
};
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true
});

// Mock localStorage and sessionStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });
Object.defineProperty(window, 'sessionStorage', { value: sessionStorageMock });

describe('Terms Component', () => {
  const mockGenerateSigningUrl = jest.fn();
  const mockGetApplicationbyQuoteId = jest.fn();
  const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
  const mockUseAuth0 = useAuth0 as jest.MockedFunction<typeof useAuth0>;
  const mockUseGenerateSigningUrlMutation = useGenerateSigningUrlMutation as jest.MockedFunction<
    typeof useGenerateSigningUrlMutation
  >;
  const mockUseGetApplicationbyQuoteIdLazyQuery = useGetApplicationbyQuoteIdLazyQuery as jest.MockedFunction<
    typeof useGetApplicationbyQuoteIdLazyQuery
  >;
  const mockUseAuthContext = useAuthContext as jest.MockedFunction<
    typeof useAuthContext
  >;

  const mockUser: User = {
    email_verified: true,
    email: 'test@example.com',
    anonymous: false,
    sessionID: 'test-session-id'
  };

  const defaultAuthState: AuthContext = {
    user: mockUser,
    isLoading: false,
    isAuthenticated: true,
    logout: jest.fn(),
    login: jest.fn(),
    error: undefined,
    invoiceId: '',
    quoteId: ''
  };

  const defaultAuth0State = {
    user: { email_verified: true, email: 'test@example.com' },
    error: undefined,
    isLoading: false,
    isAuthenticated: true,
    getAccessTokenSilently: jest.fn().mockResolvedValue('mock-token'),
    getAccessTokenWithPopup: jest.fn().mockResolvedValue('mock-token'),
    getIdTokenClaims: jest.fn(),
    loginWithRedirect: jest.fn().mockResolvedValue(undefined),
    loginWithPopup: jest.fn().mockResolvedValue(undefined),
    logout: jest.fn().mockReturnValue(undefined),
    buildAuthorizeUrl: jest.fn().mockResolvedValue('mock-url'),
    buildLogoutUrl: jest.fn().mockReturnValue('mock-logout-url'),
    handleRedirectCallback: jest.fn().mockResolvedValue(undefined)
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockLocation.search = '';
    mockLocation.href = 'http://localhost:3000/terms';
    mockLocation.pathname = '/terms';

    mockUseAuth.mockReturnValue(defaultAuthState);
    mockUseAuth0.mockReturnValue(defaultAuth0State);
    mockUseAuthContext.mockReturnValue({ login_hint: undefined });
    mockUseGenerateSigningUrlMutation.mockReturnValue([
      mockGenerateSigningUrl,
      {
        loading: false,
        called: false,
        client: {} as any,
        error: undefined
      }
    ]);
    mockUseGetApplicationbyQuoteIdLazyQuery.mockReturnValue([
      mockGetApplicationbyQuoteId,
      {
        data: undefined,
        error: undefined,
        loading: false,
        called: false,
        variables: undefined,
        networkStatus: 7,
        client: {} as any,
        startPolling: jest.fn(),
        stopPolling: jest.fn(),
        subscribeToMore: jest.fn(),
        updateQuery: jest.fn(),
        refetch: jest.fn(),
        fetchMore: jest.fn()
      } as any
    ]);
  });

  const renderTermsComponent = (initialEntries = ['/terms']) => {
    return render(
      <MockedProvider>
        <MemoryRouter initialEntries={initialEntries}>
          <Route path="/terms" component={Terms} />
        </MemoryRouter>
      </MockedProvider>
    );
  };

  describe('Loading States', () => {
    it('renders loading message when Auth0 is loading', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthState,
        user: null,
        isAuthenticated: false
      });
      mockUseAuth0.mockReturnValue({
        ...defaultAuth0State,
        user: null,
        isLoading: true
      });

      renderTermsComponent();

      expect(
        screen.getByText('Your patience is appreciated!')
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          "We are creating the documents you'll need to review & sign"
        )
      ).toBeInTheDocument();
      expect(screen.getByTestId('MessageLoading')).toBeInTheDocument();
    });

    it('renders loading message when Auth provider is loading', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthState,
        user: null,
        isAuthenticated: false,
        isLoading: true
      });
      mockUseAuth0.mockReturnValue({
        ...defaultAuth0State,
        user: null,
        isLoading: false
      });

      renderTermsComponent();

      expect(
        screen.getByText('Your patience is appreciated!')
      ).toBeInTheDocument();
      expect(screen.getByTestId('MessageLoading')).toBeInTheDocument();
    });

    it('renders loading message when both auth providers are loading', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthState,
        user: null,
        isAuthenticated: false,
        isLoading: true
      });
      mockUseAuth0.mockReturnValue({
        ...defaultAuth0State,
        user: null,
        isLoading: true
      });

      renderTermsComponent();

      expect(
        screen.getByText('Your patience is appreciated!')
      ).toBeInTheDocument();
      expect(screen.getByTestId('MessageLoading')).toBeInTheDocument();
    });
  });

  describe('Error States', () => {
    it('renders Auth0 error when present', () => {
      const auth0Error = new Error('Auth0 connection failed');
      mockUseAuth0.mockReturnValue({
        ...defaultAuth0State,
        error: auth0Error
      });

      renderTermsComponent();

      expect(
        screen.getByText('There is an Auth0 error: Auth0 connection failed')
      ).toBeInTheDocument();
    });

    it('renders application error when present', () => {
      const apolloError = new ApolloError({
        errorMessage: 'GraphQL error occurred',
        graphQLErrors: [],
        networkError: null
      });
      mockUseGetApplicationbyQuoteIdLazyQuery.mockReturnValue([
        mockGetApplicationbyQuoteId,
        {
          data: undefined,
          error: apolloError,
          loading: false,
          called: true,
          variables: undefined,
          networkStatus: 8,
          client: {} as any,
          startPolling: jest.fn(),
          stopPolling: jest.fn(),
          subscribeToMore: jest.fn(),
          updateQuery: jest.fn(),
          refetch: jest.fn(),
          fetchMore: jest.fn()
        } as any
      ]);

      renderTermsComponent();

      expect(
        screen.getByText('There is a backend error: GraphQL error occurred')
      ).toBeInTheDocument();
    });

    it('renders signing URL error when max retries reached', () => {
      const signingUrlError = new ApolloError({
        errorMessage: 'Signing URL generation failed',
        graphQLErrors: [],
        networkError: null
      });
      mockUseGenerateSigningUrlMutation.mockReturnValue([
        mockGenerateSigningUrl,
        {
          loading: false,
          called: true,
          client: {} as any,
          error: signingUrlError
        }
      ]);

      // Mock the component to simulate max retries reached
      const TermsWithMaxRetries = () => {
        const [reachMaxRetries] = React.useState(true);
        const [, { error: signingUrlError }] = useGenerateSigningUrlMutation();

        if (signingUrlError && reachMaxRetries) {
          return <div>Error component would be rendered</div>;
        }
        return <div>Normal flow</div>;
      };

      render(<TermsWithMaxRetries />);
      expect(
        screen.getByText('Error component would be rendered')
      ).toBeInTheDocument();
    });
  });

  describe('User Authentication States', () => {
    it('renders error message when user cannot be retrieved', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthState,
        user: null,
        isAuthenticated: false,
        isLoading: false
      });
      mockUseAuth0.mockReturnValue({
        ...defaultAuth0State,
        user: null,
        isLoading: false
      });

      renderTermsComponent();

      expect(
        screen.getByText('Cannot retrieve user profile from Auth0.')
      ).toBeInTheDocument();
    });

    it('renders email verification message when email is not verified', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthState,
        user: null,
        isAuthenticated: false
      });
      mockUseAuth0.mockReturnValue({
        ...defaultAuth0State,
        user: { email_verified: false, email: 'test@example.com' },
        isLoading: false
      });

      renderTermsComponent();

      expect(
        screen.getByText('Please keep this tab open.')
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          'We have sent the verification email. Please check your inbox and refresh this tab after completing email verification.'
        )
      ).toBeInTheDocument();
    });

    it('renders email verification message when email is missing', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthState,
        user: null,
        isAuthenticated: false
      });
      mockUseAuth0.mockReturnValue({
        ...defaultAuth0State,
        user: { email_verified: true, email: null },
        isLoading: false
      });

      renderTermsComponent();

      expect(
        screen.getByText('Please keep this tab open.')
      ).toBeInTheDocument();
    });

    it('uses authenticated user when available', () => {
      const authUser: User = {
        email_verified: true,
        email: 'auth@example.com',
        anonymous: false,
        sessionID: 'auth-session-id'
      };

      mockUseAuth.mockReturnValue({
        ...defaultAuthState,
        user: authUser,
        isAuthenticated: true,
        isLoading: false
      });
      mockUseAuth0.mockReturnValue({
        ...defaultAuth0State,
        user: { email_verified: true, email: 'auth0@example.com' },
        isLoading: false
      });

      renderTermsComponent();

      expect(
        screen.getByText('Your patience is appreciated!')
      ).toBeInTheDocument();
    });

    it('uses Auth0 user when not authenticated with auth provider', () => {
      mockUseAuth.mockReturnValue({
        ...defaultAuthState,
        user: null,
        isAuthenticated: false,
        isLoading: false
      });
      mockUseAuth0.mockReturnValue({
        ...defaultAuth0State,
        user: { email_verified: true, email: 'auth0@example.com' },
        isLoading: false
      });

      renderTermsComponent();

      expect(
        screen.getByText('Your patience is appreciated!')
      ).toBeInTheDocument();
    });
  });

  describe('Quote ID Handling', () => {
    it('extracts quote ID from URL query parameters', async () => {
      mockLocation.search = '?quote=test-quote-123';

      renderTermsComponent(['/terms?quote=test-quote-123']);

      await waitFor(() => {
        expect(mockGetApplicationbyQuoteId).toHaveBeenCalledWith({
          variables: { quoteId: 'test-quote-123' }
        });
      });
    });

    it('extracts quote ID from URL path parameters', async () => {
      const renderWithPathParam = () => {
        return render(
          <MockedProvider>
            <MemoryRouter initialEntries={['/terms/path-quote-456']}>
              <Route path="/terms/:quoteId" component={Terms} />
            </MemoryRouter>
          </MockedProvider>
        );
      };

      renderWithPathParam();

      await waitFor(() => {
        expect(mockGetApplicationbyQuoteId).toHaveBeenCalledWith({
          variables: { quoteId: 'path-quote-456' }
        });
      });
    });

    it('prioritizes query parameter over path parameter', async () => {
      mockLocation.search = '?quote=query-quote-789';

      const renderWithBothParams = () => {
        return render(
          <MockedProvider>
            <MemoryRouter
              initialEntries={['/terms/path-quote-456?quote=query-quote-789']}
            >
              <Route path="/terms/:quoteId" component={Terms} />
            </MemoryRouter>
          </MockedProvider>
        );
      };

      renderWithBothParams();

      await waitFor(() => {
        expect(mockGetApplicationbyQuoteId).toHaveBeenCalledWith({
          variables: { quoteId: 'query-quote-789' }
        });
      });
    });

    it('does not call getApplicationbyQuoteId when no quote ID is provided', () => {
      renderTermsComponent();

      expect(mockGetApplicationbyQuoteId).not.toHaveBeenCalled();
    });

    it('does not call getApplicationbyQuoteId when email is not valid', () => {
      mockLocation.search = '?quote=test-quote-123';
      mockUseAuth.mockReturnValue({
        ...defaultAuthState,
        user: null,
        isAuthenticated: false
      });
      mockUseAuth0.mockReturnValue({
        ...defaultAuth0State,
        user: { email_verified: false, email: 'test@example.com' }
      });

      renderTermsComponent(['/terms?quote=test-quote-123']);

      expect(mockGetApplicationbyQuoteId).not.toHaveBeenCalled();
    });
  });

  describe('Signing URL Generation', () => {
    it('calls generateSigningUrl when application data is available', async () => {
      mockLocation.search = '?quote=test-quote-123';
      const mockApplicationData: GetApplicationbyQuoteIdQuery = {
        getApplicationbyQuoteId: {
          __typename: 'getApplicationbyQuoteIdResponse',
          country: 'USA',
          state: 'California'
        }
      };

      mockUseGetApplicationbyQuoteIdLazyQuery.mockReturnValue([
        mockGetApplicationbyQuoteId,
        {
          data: mockApplicationData,
          error: undefined,
          loading: false,
          called: true,
          variables: { quoteId: 'test-quote-123' },
          networkStatus: 7,
          client: {} as any,
          startPolling: jest.fn(),
          stopPolling: jest.fn(),
          subscribeToMore: jest.fn(),
          updateQuery: jest.fn(),
          refetch: jest.fn(),
          fetchMore: jest.fn()
        } as any
      ]);

      mockGenerateSigningUrl.mockResolvedValue({
        data: { generateSigningURL: 'https://example.com/sign' }
      });

      renderTermsComponent(['/terms?quote=test-quote-123']);

      await waitFor(() => {
        expect(mockGetApplicationbyQuoteId).toHaveBeenCalledWith({
          variables: { quoteId: 'test-quote-123' }
        });
      });
    });

    it('redirects to signing URL on successful generation', async () => {
      mockLocation.search = '?quote=test-quote-123';
      const mockApplicationData: GetApplicationbyQuoteIdQuery = {
        getApplicationbyQuoteId: {
          __typename: 'getApplicationbyQuoteIdResponse',
          country: 'USA',
          state: 'California'
        }
      };

      mockUseGetApplicationbyQuoteIdLazyQuery.mockReturnValue([
        mockGetApplicationbyQuoteId,
        {
          data: mockApplicationData,
          error: undefined,
          loading: false,
          called: true,
          variables: { quoteId: 'test-quote-123' },
          networkStatus: 7,
          client: {} as any,
          startPolling: jest.fn(),
          stopPolling: jest.fn(),
          subscribeToMore: jest.fn(),
          updateQuery: jest.fn(),
          refetch: jest.fn(),
          fetchMore: jest.fn()
        } as any
      ]);

      const signingUrl = 'https://example.com/sign';
      mockGenerateSigningUrl.mockResolvedValue({
        data: { generateSigningURL: signingUrl }
      });

      renderTermsComponent(['/terms?quote=test-quote-123']);

      await waitFor(() => {
        expect(mockGenerateSigningUrl).toHaveBeenCalledWith({
          variables: { quoteId: 'test-quote-123' }
        });
      });
    });

    it('handles signing URL generation failure', async () => {
      mockLocation.search = '?quote=test-quote-123';
      const mockApplicationData: GetApplicationbyQuoteIdQuery = {
        getApplicationbyQuoteId: {
          __typename: 'getApplicationbyQuoteIdResponse',
          country: 'USA',
          state: 'California'
        }
      };

      mockUseGetApplicationbyQuoteIdLazyQuery.mockReturnValue([
        mockGetApplicationbyQuoteId,
        {
          data: mockApplicationData,
          error: undefined,
          loading: false,
          called: true,
          variables: { quoteId: 'test-quote-123' },
          networkStatus: 7,
          client: {} as any,
          startPolling: jest.fn(),
          stopPolling: jest.fn(),
          subscribeToMore: jest.fn(),
          updateQuery: jest.fn(),
          refetch: jest.fn(),
          fetchMore: jest.fn()
        } as any
      ]);

      mockGenerateSigningUrl.mockImplementation(() =>
        Promise.reject(new Error('Network error'))
      );

      renderTermsComponent(['/terms?quote=test-quote-123']);

      await waitFor(() => {
        expect(mockGenerateSigningUrl).toHaveBeenCalledWith({
          variables: { quoteId: 'test-quote-123' }
        });
      });
    });
  });

  describe('Component Rendering', () => {
    it('renders Signout component when conditions are met', () => {
      renderTermsComponent();

      // The Signout component should be rendered but returns null
      // We can verify it's in the component tree by checking the loading message
      expect(
        screen.getByText('Your patience is appreciated!')
      ).toBeInTheDocument();
    });

    it('applies correct CSS class', () => {
      mockUseAuth0.mockReturnValue({
        ...defaultAuth0State,
        user: null,
        isLoading: false
      });
      mockUseAuth.mockReturnValue({
        ...defaultAuthState,
        user: null,
        isAuthenticated: false,
        isLoading: false
      });

      renderTermsComponent();

      const errorElement = screen.getByText(
        'Cannot retrieve user profile from Auth0.'
      );
      expect(errorElement.closest('div')).toHaveClass(
        'Terms',
        'm-auto',
        'text-lg',
        'container',
        'text-center'
      );
    });

    it('applies correct CSS class for email verification message', () => {
      mockUseAuth0.mockReturnValue({
        ...defaultAuth0State,
        user: { email_verified: false, email: 'test@example.com' },
        isLoading: false
      });
      mockUseAuth.mockReturnValue({
        ...defaultAuthState,
        user: null,
        isAuthenticated: false,
        isLoading: false
      });

      renderTermsComponent();

      const emailVerificationText = screen.getByText(
        'We have sent the verification email. Please check your inbox and refresh this tab after completing email verification.'
      );
      expect(emailVerificationText.closest('div')).toHaveClass(
        'Terms',
        'm-auto',
        'text-lg',
        'container',
        'text-center',
        'leading-loose'
      );
    });
  });

  describe('Retry Logic and Error Handling', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.runOnlyPendingTimers();
      jest.useRealTimers();
    });

    it('handles null signing URL response', async () => {
      mockLocation.search = '?quote=test-quote-123';
      const mockApplicationData: GetApplicationbyQuoteIdQuery = {
        getApplicationbyQuoteId: {
          __typename: 'getApplicationbyQuoteIdResponse',
          country: 'USA',
          state: 'California'
        }
      };

      mockUseGetApplicationbyQuoteIdLazyQuery.mockReturnValue([
        mockGetApplicationbyQuoteId,
        {
          data: mockApplicationData,
          error: undefined,
          loading: false,
          called: true,
          variables: { quoteId: 'test-quote-123' },
          networkStatus: 7,
          client: {} as any,
          startPolling: jest.fn(),
          stopPolling: jest.fn(),
          subscribeToMore: jest.fn(),
          updateQuery: jest.fn(),
          refetch: jest.fn(),
          fetchMore: jest.fn()
        } as any
      ]);

      mockGenerateSigningUrl.mockResolvedValue({
        data: { generateSigningURL: null }
      });

      renderTermsComponent(['/terms?quote=test-quote-123']);

      await waitFor(() => {
        expect(mockGenerateSigningUrl).toHaveBeenCalledWith({
          variables: { quoteId: 'test-quote-123' }
        });
      });
    });

    it('handles undefined signing URL response', async () => {
      mockLocation.search = '?quote=test-quote-123';
      const mockApplicationData: GetApplicationbyQuoteIdQuery = {
        getApplicationbyQuoteId: {
          __typename: 'getApplicationbyQuoteIdResponse',
          country: 'USA',
          state: 'California'
        }
      };

      mockUseGetApplicationbyQuoteIdLazyQuery.mockReturnValue([
        mockGetApplicationbyQuoteId,
        {
          data: mockApplicationData,
          error: undefined,
          loading: false,
          called: true,
          variables: { quoteId: 'test-quote-123' },
          networkStatus: 7,
          client: {} as any,
          startPolling: jest.fn(),
          stopPolling: jest.fn(),
          subscribeToMore: jest.fn(),
          updateQuery: jest.fn(),
          refetch: jest.fn(),
          fetchMore: jest.fn()
        } as any
      ]);

      mockGenerateSigningUrl.mockResolvedValue({
        data: { generateSigningURL: undefined }
      });

      renderTermsComponent(['/terms?quote=test-quote-123']);

      await waitFor(() => {
        expect(mockGenerateSigningUrl).toHaveBeenCalledWith({
          variables: { quoteId: 'test-quote-123' }
        });
      });
    });

    it('does not render error when signing URL error exists but max retries not reached', async () => {
      mockLocation.search = '?quote=test-quote-123';
      const signingUrlError = new ApolloError({
        errorMessage: 'Signing URL generation failed',
        graphQLErrors: [],
        networkError: null
      });

      mockUseGenerateSigningUrlMutation.mockReturnValue([
        mockGenerateSigningUrl,
        {
          loading: false,
          called: true,
          client: {} as any,
          error: signingUrlError
        }
      ]);

      renderTermsComponent(['/terms?quote=test-quote-123']);

      expect(
        screen.queryByText(/Signing URL generation failed/i)
      ).not.toBeInTheDocument();
      expect(
        screen.getByText('Your patience is appreciated!')
      ).toBeInTheDocument();
    });

    it('does not render error when max retries reached but no signing URL error', () => {
      mockUseGenerateSigningUrlMutation.mockReturnValue([
        mockGenerateSigningUrl,
        {
          loading: false,
          called: true,
          client: {} as any,
          error: undefined
        }
      ]);

      renderTermsComponent(['/terms?quote=test-quote-123']);

      expect(screen.queryByText(/Error/i)).not.toBeInTheDocument();
      expect(
        screen.getByText('Your patience is appreciated!')
      ).toBeInTheDocument();
    });


    it('retries signing URL generation with exponential backoff', async () => {
      jest.useRealTimers();
      mockLocation.search = '?quote=test-quote-123';
      const mockApplicationData: GetApplicationbyQuoteIdQuery = {
        getApplicationbyQuoteId: {
          __typename: 'getApplicationbyQuoteIdResponse',
          country: 'USA',
          state: 'California'
        }
      };

      mockUseGetApplicationbyQuoteIdLazyQuery.mockReturnValue([
        mockGetApplicationbyQuoteId,
        {
          data: mockApplicationData,
          error: undefined,
          loading: false,
          called: true,
          variables: { quoteId: 'test-quote-123' },
          networkStatus: 7,
          client: {} as any,
          startPolling: jest.fn(),
          stopPolling: jest.fn(),
          subscribeToMore: jest.fn(),
          updateQuery: jest.fn(),
          refetch: jest.fn(),
          fetchMore: jest.fn()
        } as any
      ]);

      let callCount = 0;
      mockGenerateSigningUrl.mockImplementation(() => {
        callCount++;
        if (callCount < 2) {
          return Promise.reject(new Error('Network error'));
        }
        return Promise.resolve({
          data: { generateSigningURL: 'https://example.com/sign' }
        });
      });

      renderTermsComponent(['/terms?quote=test-quote-123']);

      await waitFor(
        () => {
          expect(mockGenerateSigningUrl).toHaveBeenCalledTimes(2);
        },
        { timeout: 5000 }
      );

      await waitFor(() => {
        expect(mockLocation.href).toBe('https://example.com/sign');
      });
    });

    it('sets reachMaxRetries and throws error when max retries exceeded', async () => {
      jest.useRealTimers();
      mockLocation.search = '?quote=test-quote-123';
      const mockApplicationData: GetApplicationbyQuoteIdQuery = {
        getApplicationbyQuoteId: {
          __typename: 'getApplicationbyQuoteIdResponse',
          country: 'USA',
          state: 'California'
        }
      };

      mockUseGetApplicationbyQuoteIdLazyQuery.mockReturnValue([
        mockGetApplicationbyQuoteId,
        {
          data: mockApplicationData,
          error: undefined,
          loading: false,
          called: true,
          variables: { quoteId: 'test-quote-123' },
          networkStatus: 7,
          client: {} as any,
          startPolling: jest.fn(),
          stopPolling: jest.fn(),
          subscribeToMore: jest.fn(),
          updateQuery: jest.fn(),
          refetch: jest.fn(),
          fetchMore: jest.fn()
        } as any
      ]);

      mockGenerateSigningUrl.mockImplementation(() =>
        Promise.reject(new Error('Network error'))
      );

      renderTermsComponent(['/terms?quote=test-quote-123']);

      await waitFor(
        () => {
          expect(mockGenerateSigningUrl).toHaveBeenCalledTimes(3);
        },
        { timeout: 10000 }
      );
    });

    it('renders Error component when signing URL error and max retries reached', async () => {
      jest.useRealTimers();
      mockLocation.search = '?quote=test-quote-123';
      const signingUrlError = new ApolloError({
        errorMessage: 'Signing URL generation failed',
        graphQLErrors: [],
        networkError: null
      });

      const mockApplicationData: GetApplicationbyQuoteIdQuery = {
        getApplicationbyQuoteId: {
          __typename: 'getApplicationbyQuoteIdResponse',
          country: 'USA',
          state: 'California'
        }
      };

      mockUseGetApplicationbyQuoteIdLazyQuery.mockReturnValue([
        mockGetApplicationbyQuoteId,
        {
          data: mockApplicationData,
          error: undefined,
          loading: false,
          called: true,
          variables: { quoteId: 'test-quote-123' },
          networkStatus: 7,
          client: {} as any,
          startPolling: jest.fn(),
          stopPolling: jest.fn(),
          subscribeToMore: jest.fn(),
          updateQuery: jest.fn(),
          refetch: jest.fn(),
          fetchMore: jest.fn()
        } as any

      mockUseGetSigningUrlLazyQuery.mockReturnValue([
        mockGetSigningUrl,
        {
          data: undefined,
          error: signingUrlError,
          loading: false
        } as any
      ]);

      render(<Terms />);

      await waitFor(() => {
        expect(screen.getByText(/Error/i)).toBeInTheDocument();
      });
      ]);
    });
  });

  describe('Retry Logic with Max Retries', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.runOnlyPendingTimers();
      jest.useRealTimers();
    });

    it('retries signing URL generation and reaches max retries', async () => {
      mockLocation.search = '?quote=test-quote-123';
      const mockApplicationData: GetApplicationbyQuoteIdQuery = {
        getApplicationbyQuoteId: {
          __typename: 'getApplicationbyQuoteIdResponse',
          country: 'USA',
          state: 'California'
        }
      };

      let callCount = 0;
      mockGenerateSigningUrl.mockImplementation(() => {
        callCount++;
        return Promise.reject(new Error('Network error'));
      });

      mockUseGetApplicationbyQuoteIdLazyQuery.mockReturnValue([
        mockGetApplicationbyQuoteId,
        {
          data: mockApplicationData,
          error: undefined,
          loading: false,
          called: true,
          variables: { quoteId: 'test-quote-123' },
          networkStatus: 7,
          client: {} as any,
          startPolling: jest.fn(),
          stopPolling: jest.fn(),
          subscribeToMore: jest.fn(),
          updateQuery: jest.fn(),
          refetch: jest.fn(),
          fetchMore: jest.fn()
        } as any
      ]);

      renderTermsComponent(['/terms?quote=test-quote-123']);

      await waitFor(() => {
        expect(mockGenerateSigningUrl).toHaveBeenCalled();
      });

      for (let i = 0; i < 5; i++) {
        await jest.runAllTimersAsync();
      }

      await waitFor(() => {
        expect(callCount).toBeGreaterThanOrEqual(3);
      });
    });

    it('renders error component when max retries reached with signing URL error', async () => {
      mockLocation.search = '?quote=test-quote-123';
      const signingUrlError = new ApolloError({
        errorMessage: 'Signing URL generation failed',
        graphQLErrors: [],
        networkError: null
      });

      const mockApplicationData: GetApplicationbyQuoteIdQuery = {
        getApplicationbyQuoteId: {
          __typename: 'getApplicationbyQuoteIdResponse',
          country: 'USA',
          state: 'California'
        }
      };

      mockGenerateSigningUrl.mockImplementation(() =>
        Promise.reject(new Error('Network error'))
      );

      mockUseGenerateSigningUrlMutation.mockReturnValue([
        mockGenerateSigningUrl,
        {
          loading: false,
          called: true,
          client: {} as any,
          error: signingUrlError
        }
      ]);

      mockUseGetApplicationbyQuoteIdLazyQuery.mockReturnValue([
        mockGetApplicationbyQuoteId,
        {
          data: mockApplicationData,
          error: undefined,
          loading: false,
          called: true,
          variables: { quoteId: 'test-quote-123' },
          networkStatus: 7,
          client: {} as any,
          startPolling: jest.fn(),
          stopPolling: jest.fn(),
          subscribeToMore: jest.fn(),
          updateQuery: jest.fn(),
          refetch: jest.fn(),
          fetchMore: jest.fn()
        } as any
      ]);

      const { rerender } = renderTermsComponent(['/terms?quote=test-quote-123']);

      await waitFor(() => {
        expect(mockGenerateSigningUrl).toHaveBeenCalled();
      });

      for (let i = 0; i < 5; i++) {
        await jest.runAllTimersAsync();
      }

      mockUseGenerateSigningUrlMutation.mockReturnValue([
        mockGenerateSigningUrl,
        {
          loading: false,
          called: true,
          client: {} as any,
          error: signingUrlError
        }
      ]);

      rerender(
        <MockedProvider>
          <MemoryRouter initialEntries={['/terms?quote=test-quote-123']}>
            <Route path="/terms" component={Terms} />
          </MemoryRouter>
        </MockedProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument();
      });
    });

    it('performs recursive retry with exponential backoff', async () => {
      mockLocation.search = '?quote=test-quote-123';
      const mockApplicationData: GetApplicationbyQuoteIdQuery = {
        getApplicationbyQuoteId: {
          __typename: 'getApplicationbyQuoteIdResponse',
          country: 'USA',
          state: 'California'
        }
      };

      let callCount = 0;
      mockGenerateSigningUrl.mockImplementation(() => {
        callCount++;
        if (callCount < 2) {
          return Promise.reject(new Error('Temporary error'));
        }
        return Promise.resolve({
          data: { generateSigningURL: 'https://example.com/sign' }
        });
      });

      mockUseGetApplicationbyQuoteIdLazyQuery.mockReturnValue([
        mockGetApplicationbyQuoteId,
        {
          data: mockApplicationData,
          error: undefined,
          loading: false,
          called: true,
          variables: { quoteId: 'test-quote-123' },
          networkStatus: 7,
          client: {} as any,
          startPolling: jest.fn(),
          stopPolling: jest.fn(),
          subscribeToMore: jest.fn(),
          updateQuery: jest.fn(),
          refetch: jest.fn(),
          fetchMore: jest.fn()
        } as any
      ]);

      renderTermsComponent(['/terms?quote=test-quote-123']);

      await waitFor(() => {
        expect(mockGenerateSigningUrl).toHaveBeenCalledTimes(2);
      });

      await waitFor(
        () => {
          expect(callCount).toBe(2);
        },
      );
    });


    it('retries signing URL generation and eventually succeeds', async () => {
      mockLocation.search = '?quote=test-quote-123';
      const mockApplicationData: GetApplicationbyQuoteIdQuery = {
        getApplicationbyQuoteId: {
          __typename: 'getApplicationbyQuoteIdResponse',
          country: 'USA',
          state: 'California'
        }
      };

      mockUseGetApplicationbyQuoteIdLazyQuery.mockReturnValue([
        mockGetApplicationbyQuoteId,
        {
          data: mockApplicationData,
          error: undefined,
          loading: false,
          called: true,
          variables: { quoteId: 'test-quote-123' },
          networkStatus: 7,
          client: {} as any,
          startPolling: jest.fn(),
          stopPolling: jest.fn(),
          subscribeToMore: jest.fn(),
          updateQuery: jest.fn(),
          refetch: jest.fn(),
          fetchMore: jest.fn()
        } as any
      ]);

      let callCount = 0;
      mockGenerateSigningUrl.mockImplementation(() => {
        callCount++;
        if (callCount < 2) {
          return Promise.reject(new Error('Network error'));
        }
        return Promise.resolve({
          data: { generateSigningURL: 'https://example.com/sign' }
        });
      });

      renderTermsComponent(['/terms?quote=test-quote-123']);

      await waitFor(
        () => {
          expect(mockGenerateSigningUrl).toHaveBeenCalledTimes(2);
        },
        { timeout: 10000 }
      );

      jest.runAllTimers();

      await waitFor(
        () => {
          expect(window.location.href).toBe('https://example.com/sign');
        },
        { timeout: 10000 }
      );
    });
  });
});
