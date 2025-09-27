import type { Candidate, Company, User } from "@/types";
import { useEffect, useState, type ReactNode } from "react";
import { GlobalContext } from "./GlobalContextExport";
import { useNavigate } from "react-router-dom";
import { usePrivy, useWallets } from "@privy-io/react-auth";
import { flowTestnet } from "viem/chains";
import {
  createPublicClient,
  createWalletClient,
  custom,
  formatEther,
  type Hex,
  type PublicClient,
  type WalletClient,
} from "viem";

const mockUsers: User[] = [
  {
    id: "1",
    email: "company@demo.com",
    name: "Tech Innovators Inc",
    type: "company",
    createdAt: "2024-01-01",
    companyName: "Tech Innovators Inc",
    industry: "Technology",
    size: "100-500",
    description: "Leading AI and software development company",
    website: "https://techinnovators.com",
  } as Company,
  {
    id: "2",
    email: "candidate@demo.com",
    name: "John Developer",
    type: "candidate",
    createdAt: "2024-01-01",
    title: "Senior Frontend Developer",
    experience: 5,
    skills: ["React", "TypeScript", "Node.js", "Python"],
    location: "San Francisco, CA",
    bio: "Passionate full-stack developer with 5+ years of experience",
    education: "BS Computer Science",
    phone: "+1-555-0123",
  } as Candidate,
];

const CONTRACT_ADDRESS = "0x008ad8bc881E39A73DA3E0bEE77A6a004b06f67d";

export function GlobalContextProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const { wallets } = useWallets();
  const { ready } = usePrivy();

  const [jobPublicClient, setJobPublicClient] = useState<
    PublicClient | undefined
  >();
  const [jobWalletClient, setJobWalletClient] = useState<
    WalletClient | undefined
  >();

  useEffect(() => {
    // Check for stored auth
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    if (ready) {
      (async function () {
        const privyProvider = await wallets[0].getEthereumProvider();

        await wallets[0].switchChain(flowTestnet.id);

        const publicClient = createPublicClient({
          chain: flowTestnet,
          transport: custom(privyProvider),
        });

        const balance1 = await publicClient.getBalance({
          address: wallets[0].address as Hex,
        });
        console.log(formatEther(balance1), "formatted");

        const walletClient = await createWalletClient({
          account: wallets[0].address as Hex,
          chain: flowTestnet,
          transport: custom(privyProvider),
        });

        setJobPublicClient(publicClient);
        setJobWalletClient(walletClient);
      })();
    }
  }, [wallets]);

  const login = async (
    email: string,
    _password: string,
    type: "company" | "candidate"
  ) => {
    setLoading(true);
    // Mock authentication
    const foundUser = mockUsers.find(
      (u) => u.email === email && u.type === type
    );

    if (foundUser) {
      setUser(foundUser);
      localStorage.setItem("user", JSON.stringify(foundUser));
      navigate(`/${type}`);
    } else {
      // Fallback to creating a mock user based on type
      const mockUser = type === "company" ? mockUsers[0] : mockUsers[1];
      setUser(mockUser);
      localStorage.setItem("user", JSON.stringify(mockUser));
      navigate(`/${type}`);
    }

    setLoading(false);
  };

  const register = async (
    userData: Partial<User>,
    type: "company" | "candidate"
  ) => {
    setLoading(true);
    // Mock registration
    const newUser: User = {
      id: Date.now().toString(),
      email: userData.email!,
      name: userData.name!,
      type,
      createdAt: new Date().toISOString(),
      ...userData,
    };

    setUser(newUser);
    localStorage.setItem("user", JSON.stringify(newUser));
    setLoading(false);
  };

  const logout = () => {
    setUser(null);
    navigate("/");
    localStorage.removeItem("user");
  };

  useEffect(() => {
    if (!jobPublicClient) return;
    (async function () {
      const balance = await jobPublicClient?.getBalance({
        address: "0xFB1322eC42f890Cd7b4BC26AD697abb917Db1517" as Hex,
      });
      console.log(formatEther(balance), "Balance in wei");
    })();
  }, [jobPublicClient]);

  return (
    <GlobalContext.Provider
      value={{
        user,
        login,
        register,
        logout,
        loading,
        jobPublicClient,
        jobWalletClient,
        contractAddress: CONTRACT_ADDRESS,
      }}
    >
      {children}
    </GlobalContext.Provider>
  );
}