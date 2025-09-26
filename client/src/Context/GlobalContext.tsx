import { createContext, type ReactNode } from "react";

interface GlobalContextType {}

export const GlobalContext = createContext<GlobalContextType>({});

export default function GlobalContextProvider({
  children,
}: {
  children: ReactNode;
}) {
  return <GlobalContext.Provider value={{}}>{children}</GlobalContext.Provider>;
}
