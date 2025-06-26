import { useEffect, useState } from "react";
import { supabase } from "../utils/supabaseClient";
 
export default function Home() {
    const [session, setSession] = useState(null);
 
    useEffect(() => {
        setSession(supabase.auth.getSession());
        const { data: listener } = supabase.auth.onAuthStateChange(
            (_event, session) => {
                setSession(session);
            }
        );
        return () => listener.subscription.unsubscribe();
    }, []);
 
    return (
        <div>
            <h1>Supabase Auth Example</h1>
            {session ? <p>Logged in</p> : <p>Not logged in</p>}
        </div>
    );
}