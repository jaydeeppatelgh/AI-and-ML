import { useState } from 'react'; export default function Home() {
    const [prompt, setPrompt] = useState(''); const [response, setResponse] = useState(''); const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault(); setLoading(true); setResponse('');
        const res = await fetch('/api/openai', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt }),
        });
        const data = await res.json(); setResponse(data.result); setLoading(false);
    };

    return (
        <div>
            <form onSubmit={handleSubmit}>
                <input value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="Ask something..." />
                <button type="submit">Send</button>
            </form>
            {loading && <p>Loading...</p>}
            {response && <p>Response: {response}</p>}
        </div >
    );
}
