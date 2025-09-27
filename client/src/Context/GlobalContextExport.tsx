import type { User } from "@/types";
import { createContext } from "react";
import { type User as PrivyUser } from "@privy-io/react-auth";
import type { PublicClient, WalletClient } from "viem";

interface GlobalContextType {
  user: User | null;
  privyUser?: PrivyUser | null;
  login: (
    email: string,
    password: string,
    type: "company" | "candidate"
  ) => Promise<void>;
  register: (
    userData: Partial<User>,
    type: "company" | "candidate"
  ) => Promise<void>;
  logout: () => void;
  loading: boolean;
  jobPublicClient: PublicClient | undefined;
  jobWalletClient: WalletClient | undefined;
  contractAddress: string;
}

export const GlobalContext = createContext<GlobalContextType>({
  user: null,
  login: async () => {},
  register: async () => {},
  logout: () => {},
  loading: false,
  jobPublicClient: undefined,
  jobWalletClient: undefined,
  contractAddress: "",
});