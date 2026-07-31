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
import { authenticationService } from "./service";
import { purgeProtectedLocalData } from "../privacy/localDataPurge";
import { accountApi } from "../account/api";
import type {
  AuthenticatedUserSnapshot,
  AuthenticationState,
} from "./types";

interface AuthenticationContextValue {
  state: AuthenticationState;
  login(email: string, password: string): Promise<void>;
  register(email: string, password: string): Promise<void>;
  deactivateAccount(password: string): Promise<void>;
  setOfflineLimited(user: AuthenticatedUserSnapshot): void;
  signOut(): Promise<void>;
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
    const unsubscribe = authenticationService.subscribeSessionRejected((message) => {
      if (active) {
        setState({ status: "unauthenticated", message });
      }
    });
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
      unsubscribe();
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const user = await authenticationService.login({ email, password });
    setState({ status: "authenticated", user });
  }, []);
  const register = useCallback(async (email: string, password: string) => {
    const user = await authenticationService.register({ email, password });
    setState({ status: "authenticated", user });
  }, []);
  const setOfflineLimited = useCallback(
    (user: AuthenticatedUserSnapshot) => {
      setState({ status: "offline_limited", user });
    },
    [],
  );
  const signOut = useCallback(async () => {
    setState({ status: "loading" });
    let serverStatus: "confirmed" | "not_required" | "unconfirmed" =
      "unconfirmed";
    try {
      serverStatus = await authenticationService.logout();
    } finally {
      authenticationService.lockProtectedSession();
      const purgeResult = await purgeProtectedLocalData();
      let message: string | undefined;
      if (purgeResult.status === "partial") {
        message =
          "Protected access is locked, but some local data needs cleanup retry.";
      } else if (serverStatus === "unconfirmed") {
        message =
          "Signed out on this device. Server confirmation was unavailable.";
      }
      setState({ status: "unauthenticated", message });
    }
  }, []);
  const deactivateAccount = useCallback(async (password: string) => {
    await accountApi.deactivate(password);
  }, []);
  const value = useMemo(
    () => ({
      state,
      login,
      register,
      deactivateAccount,
      setOfflineLimited,
      signOut,
    }),
    [state, login, register, deactivateAccount, setOfflineLimited, signOut],
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
