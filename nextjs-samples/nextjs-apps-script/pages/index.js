import { useState } from 'react'; export default function Home() {
    const [name, setName] = useState(''); const [result, setResult] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        const res = await fetch('YOUR_DEPLOYED_APPS_SCRIPT_URL', {
            method: 'POST',
            body: JSON.stringify({ name }),
            headers: { 'Content-Type': 'application/json' },
        });
        const data = await res.json(); setResult(data.result);
    };

    return (
        <form onSubmit={handleSubmit}>
            <input value={name} onChange={e => setName(e.target.value)} placeholder="Name" />
            <button type="submit">Send to Apps Script</button>
            {result && <p>{result}</p>}
        </form>
    );
}    