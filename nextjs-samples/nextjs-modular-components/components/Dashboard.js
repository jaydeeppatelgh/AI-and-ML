import Balance from "./Finance/Balance";
import Transactions from "./Finance/Transactions";
export default function Dashboard({ balance, transactions }) {
  return (
    <div>
      <h2>Dashboard</h2>
      <Balance amount={balance} />
      <Transactions items={transactions} />
    </div>
  );
}
