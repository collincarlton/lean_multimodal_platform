function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents || "{}");
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName("DirectoryLeads") || ss.insertSheet("DirectoryLeads");
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(["Timestamp", "Niche", "Provider", "CustomerName", "Phone", "Notes"]);
    }
    sheet.appendRow([new Date(), data.niche_slug || "", data.provider || "", data.name || "", data.phone || "", data.notes || ""]);
    return ContentService.createTextOutput(JSON.stringify({ ok: true })).setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ ok: false, error: err.toString() })).setMimeType(ContentService.MimeType.JSON);
  }
}
