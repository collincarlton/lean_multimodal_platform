function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents || "{}");
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName("DirectoryLeads") || ss.insertSheet("DirectoryLeads");
    if (sheet.getLastRow() === 0) {
      sheet.appendRow([
        "Timestamp",
        "Niche",
        "Provider",
        "CustomerName",
        "Phone",
        "Notes",
        "TCPA_1to1_Consent",
        "RiskTier",
        "DispatchStatus"
      ]);
    }
    var tcpaConsent = Boolean(data.tcpa_1to1_consent);
    var hasHitlToken = Boolean(data.hitl_confirmation_token && String(data.hitl_confirmation_token).length >= 8);
    var dispatchStatus = (tcpaConsent && hasHitlToken)
      ? "DISPATCHED_WITH_R3_HITL_TOKEN"
      : "QUEUED_AWAITING_R3_HITL_APPROVAL";
    sheet.appendRow([
      new Date(),
      data.niche_slug || "",
      data.provider || "",
      data.name || "",
      data.phone || "",
      data.notes || "",
      tcpaConsent,
      "R3_CLASS_2_EXTERNAL_COMMERCIAL",
      dispatchStatus
    ]);
    return ContentService.createTextOutput(
      JSON.stringify({
        ok: true,
        risk_tier: "R3_CLASS_2_EXTERNAL_COMMERCIAL",
        tcpa_1to1_consent: tcpaConsent,
        dispatch_status: dispatchStatus
      })
    ).setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ ok: false, error: err.toString() })).setMimeType(ContentService.MimeType.JSON);
  }
}
