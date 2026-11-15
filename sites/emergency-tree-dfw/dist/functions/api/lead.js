export async function onRequestPost(context) {
  try {
    const body = await context.request.json();
    const lead = {
      niche_slug: body.niche_slug || "emergency-tree-dfw",
      provider: body.provider || "Direct Match",
      name: String(body.name || "").slice(0, 120),
      phone: String(body.phone || "").slice(0, 40),
      notes: String(body.notes || "").slice(0, 600),
      received_at: new Date().toISOString()
    };
    if (!lead.phone) {
      return new Response(JSON.stringify({ ok: false, error: "phone_required" }), { status: 400 });
    }
    if (context.env && context.env.GAS_WEBHOOK_URL) {
      await fetch(context.env.GAS_WEBHOOK_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(lead)
      });
    }
    return new Response(JSON.stringify({ ok: true, status: "routed", provider: lead.provider }), {
      status: 200,
      headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" }
    });
  } catch (err) {
    return new Response(JSON.stringify({ ok: false, error: "server_error" }), { status: 500 });
  }
}
