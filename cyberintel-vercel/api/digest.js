// api/digest.js
// Vercel serverless function - fetches digest data from Supabase

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");

  if (req.method === "OPTIONS") return res.status(200).end();
  if (req.method !== "GET")    return res.status(405).json({ error: "Method not allowed" });

  const supabaseUrl = process.env.SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseKey) {
    return res.status(500).json({ error: "Supabase env vars not configured" });
  }

  try {
    // Fetch last 30 digests ordered by date
    const response = await fetch(
      `${supabaseUrl}/rest/v1/digests?select=*&order=created_at.desc&limit=30`,
      {
        headers: {
          "apikey":        supabaseKey,
          "Authorization": `Bearer ${supabaseKey}`,
          "Content-Type":  "application/json"
        }
      }
    );

    if (!response.ok) {
      const err = await response.text();
      return res.status(response.status).json({ error: err });
    }

    const rows = await response.json();

    // Parse items JSON string back to array
    const digests = rows.map(row => ({
      ...row,
      items: typeof row.items === "string" ? JSON.parse(row.items) : row.items
    }));

    return res.status(200).json({ digests });

  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
}
