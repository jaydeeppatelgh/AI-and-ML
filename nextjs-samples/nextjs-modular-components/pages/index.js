import Dashboard from "../components/Dashboard";

export default function Home() {
  return (
    <Dashboard
      balance={1234.56}
      transactions={["Deposit $500", "Withdraw $100"]}
    />
  );
}
