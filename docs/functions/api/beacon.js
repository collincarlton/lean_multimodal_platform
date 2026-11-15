export async function onRequestPost(context) {
  try {
    const body = await context.request.json();
    const record = {
      niche_slug: body.niche_slug || "unknown",
      event_type: body.event_type || "page_view",
      provider_slug: body.provider_slug || "",
      page_url: body.page_url || "/",
      timestamp: new Date().toISOString()
    };
    if (context.env && context.env.BEACON_WEBHOOK_URL) {
      await fetch(context.env.BEACON_WEBHOOK_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(record)
      }).catch(() => {});
    }
    return new Response(JSON.stringify({ ok: true, recorded: record.event_type }), {
      status: 200,
      headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" }
    });
  } catch (err) {
    return new Response(JSON.stringify({ ok: false, error: "invalid_json" }), { status: 400 });
  }
}
