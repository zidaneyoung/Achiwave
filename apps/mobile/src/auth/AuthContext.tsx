import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { bootstrapAuthentication } from "./bootstrap";
import type {
  AuthenticatedUserSnapshot,
  AuthenticationState,
} from "./types";

interface AuthenticationContextValue {
  state: AuthenticationState;
  setAuthenticated(user: AuthenticatedUserSnapshot): void;
  setOfflineLimited(user: AuthenticatedUserSnapshot): void;
  signOutLocally(): void;
}

const AuthenticationContext = createContext<
  AuthenticationContextValue | undefined
>(undefined);

interface AuthenticationProviderProps {
  children: ReactNode;
}

export function AuthenticationProvider({
  children,
}: AuthenticationProviderProps) {
  const [state, setState] = useState<AuthenticationState>({
    status: "loading",
  });

  useEffect(() => {
    let active = true;
    void bootstrapAuthentication()
      .then((resolvedState) => {
        if (active) {
          setState(resolvedState);
        }
      })
      .catch(() => {
        if (active) {
          setState({
            status: "failure",
            message: "Authentication could not be restored safely.",
          });
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const setAuthenticated = useCallback(
    (user: AuthenticatedUserSnapshot) => {
      setState({ status: "authenticated", user });
    },
    [],
  );
  const setOfflineLimited = useCallback(
    (user: AuthenticatedUserSnapshot) => {
      setState({ status: "offline_limited", user });
    },
    [],
  );
  const signOutLocally = useCallback(() => {
    setState({ status: "unauthenticated" });
  }, []);
  const value = useMemo(
    () => ({ state, setAuthenticated, setOfflineLimited, signOutLocally }),
    [state, setAuthenticated, setOfflineLimited, signOutLocally],
  );

  return (
    <AuthenticationContext.Provider value={value}>
      {children}
    </AuthenticationContext.Provider>
  );
}

export function useAuthentication(): AuthenticationContextValue {
  const context = useContext(AuthenticationContext);
  if (context === undefined) {
    throw new Error(
      "useAuthentication must be used inside AuthenticationProvider.",
    );
  }
  return context;
}
