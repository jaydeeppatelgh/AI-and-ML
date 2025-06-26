export default async function handler(req, res) {
    // Simulate async OpenAI call const { prompt } = req.body;
    // Normally you'd call OpenAI API here
    setTimeout(() => {
        res.status(200).json({ result: `AI response for: ${prompt}` });
    }, 1500);
}
    