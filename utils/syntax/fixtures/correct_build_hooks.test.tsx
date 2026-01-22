// From @reduxjs/toolkit - buildHooks.test.tsx (correct version)
import { render, screen, waitFor } from '@testing-library/react'

describe('hooks tests', () => {
  describe('useQuery', () => {
    test('useQuery hook basic render count assumptions', async () => {
      function User() {
        const { isFetching } = api.endpoints.getUser.useQuery(1)
        return (
          <div>
            <div data-testid="isFetching">{String(isFetching)}</div>
          </div>
        )
      }

      render(<User />, { wrapper: storeRef.wrapper })
      expect(getRenderCount()).toBe(2)

      await waitFor(() =>
        expect(screen.getByTestId('isFetching').textContent).toBe('false'),
      )
      expect(getRenderCount()).toBe(3)
    });

    test('useQuery hook sets isFetching=true whenever a request is in flight', async () => {
      function User() {
        const [value, setValue] = useState(0)

        const { isFetching } = api.endpoints.getUser.useQuery(1, {
          skip: value < 1,
        })

        return (
          <div>
            <div data-testid="isFetching">{String(isFetching)}</div>
            <button onClick={() => setValue((val) => val + 1)}>
              Increment value
            </button>
          </div>
        )
      }

      render(<User />, { wrapper: storeRef.wrapper })
      expect(getRenderCount()).toBe(1)

      await waitFor(() =>
        expect(screen.getByTestId('isFetching').textContent).toBe('false'),
      )
      fireEvent.click(screen.getByText('Increment value'))
      await waitFor(() =>
        expect(screen.getByTestId('isFetching').textContent).toBe('true'),
      )
      await waitFor(() =>
        expect(screen.getByTestId('isFetching').textContent).toBe('false'),
      )
      expect(getRenderCount()).toBe(4)
    });

    test('useQuery hook sets isLoading=true only on initial request', async () => {
      let refetch: any, isLoading: boolean, isFetching: boolean
      function User() {
        const [value, setValue] = useState(0)

        ;({ isLoading, isFetching, refetch } = api.endpoints.getUser.useQuery(
          2,
          {
            skip: value < 1,
          },
        ))
        return (
          <div>
            <div data-testid="isLoading">{String(isLoading)}</div>
            <div data-testid="isFetching">{String(isFetching)}</div>
            <button onClick={() => setValue((val) => val + 1)}>
              Increment value
            </button>
          </div>
        )
      }

      render(<User />, { wrapper: storeRef.wrapper })
      await waitFor(() =>
        expect(screen.getByTestId('isLoading').textContent).toBe('false'),
      )
    });
  });
});
