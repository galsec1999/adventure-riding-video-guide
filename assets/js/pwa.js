const installButton = document.querySelector("#install-app-button");
const installHelpButton = document.querySelector("#install-help-button");
const installHelpDialog = document.querySelector("#install-help-dialog");
const updateBanner = document.querySelector("#pwa-update-banner");
const updateMessage = document.querySelector("#pwa-update-message");
const updateButton = document.querySelector("#pwa-update-button");
const updateDismiss = document.querySelector("#pwa-update-dismiss");
const liveRegion = document.querySelector("#live-region");

let deferredInstallPrompt = null;
let waitingWorker = null;
let refreshApproved = false;

function englishMode() {
  return document.documentElement.lang === "en";
}

function isStandalone() {
  return window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
}

function reportHorizontalOverflow() {
  document.documentElement.dataset.horizontalOverflow = String(
    document.documentElement.scrollWidth > document.documentElement.clientWidth
  );
}

function announce(he, en) {
  if (liveRegion) liveRegion.textContent = englishMode() ? en : he;
}

function syncLabels() {
  const en = englishMode();
  const labels = en ? {
    kicker: "Quick access from your home screen",
    title: "Install the app",
    androidTitle: "Chrome on Android",
    androidCopy: "Open the ⋮ menu and choose “Install app” or “Add to Home screen”.",
    desktopTitle: "Chrome on desktop",
    desktopCopy: "Use the install icon in the address bar, or open the menu and choose “Install”.",
    iosTitle: "iPhone and iPad",
    iosCopy: "Open Share and choose “Add to Home Screen”.",
    offline: "YouTube videos require internet access. The library, search and learning paths remain available after the first load.",
    close: "Close installation instructions",
  } : {
    kicker: "גישה מהירה גם מהמסך הראשי",
    title: "התקנת האפליקציה",
    androidTitle: "Chrome ב־Android",
    androidCopy: "פתחו את תפריט ⋮ ובחרו “התקנת האפליקציה” או “הוספה למסך הבית”.",
    desktopTitle: "Chrome במחשב",
    desktopCopy: "לחצו על סמל ההתקנה בשורת הכתובת, או פתחו את התפריט ובחרו “Install”.",
    iosTitle: "iPhone ו־iPad",
    iosCopy: "פתחו Share ובחרו “Add to Home Screen”.",
    offline: "הסרטונים עצמם דורשים חיבור לאינטרנט. הספרייה, החיפוש והמסלולים נשארים זמינים לאחר טעינה ראשונה.",
    close: "סגירת הוראות ההתקנה",
  };
  if (installButton) installButton.textContent = en ? "Install app" : "התקנת האפליקציה";
  if (installHelpButton) installHelpButton.textContent = en ? "Installation help" : "הוראות התקנה";
  if (updateMessage) updateMessage.textContent = en ? "A new version is available." : "גרסה חדשה זמינה.";
  if (updateButton) updateButton.textContent = en ? "Update now" : "עדכון עכשיו";
  if (updateDismiss) updateDismiss.textContent = en ? "Later" : "לא עכשיו";
  const textTargets = {
    "#install-help-kicker": labels.kicker,
    "#install-help-title": labels.title,
    "#install-android-title": labels.androidTitle,
    "#install-android-copy": labels.androidCopy,
    "#install-desktop-title": labels.desktopTitle,
    "#install-desktop-copy": labels.desktopCopy,
    "#install-ios-title": labels.iosTitle,
    "#install-ios-copy": labels.iosCopy,
    "#install-offline-note": labels.offline,
  };
  Object.entries(textTargets).forEach(([selector, value]) => {
    const element = document.querySelector(selector);
    if (element) element.textContent = value;
  });
  document.querySelector("#install-help-close")?.setAttribute("aria-label", labels.close);
}

function showUpdate(worker) {
  waitingWorker = worker;
  if (updateBanner) updateBanner.hidden = false;
}

function trackInstalling(registration) {
  const worker = registration.installing;
  if (!worker) return;
  worker.addEventListener("statechange", () => {
    if (worker.state === "installed" && navigator.serviceWorker.controller) showUpdate(worker);
  });
}

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  deferredInstallPrompt = event;
  document.documentElement.dataset.installPrompt = "available";
  if (installButton && !isStandalone()) installButton.hidden = false;
});

window.addEventListener("appinstalled", () => {
  deferredInstallPrompt = null;
  document.documentElement.dataset.installPrompt = "installed";
  if (installButton) installButton.hidden = true;
  announce("האפליקציה הותקנה בהצלחה.", "The app was installed successfully.");
});

installButton?.addEventListener("click", async () => {
  if (!deferredInstallPrompt) return;
  const promptEvent = deferredInstallPrompt;
  deferredInstallPrompt = null;
  installButton.hidden = true;
  await promptEvent.prompt();
  const choice = await promptEvent.userChoice;
  if (choice.outcome !== "accepted") {
    announce("ההתקנה בוטלה. אפשר לנסות שוב מתפריט הדפדפן.", "Installation was dismissed. You can retry from the browser menu.");
  }
});

installHelpButton?.addEventListener("click", () => installHelpDialog?.showModal());
updateDismiss?.addEventListener("click", () => {
  if (updateBanner) updateBanner.hidden = true;
});
updateButton?.addEventListener("click", () => {
  if (!waitingWorker) return;
  refreshApproved = true;
  waitingWorker.postMessage({ type: "SKIP_WAITING" });
});

window.matchMedia("(display-mode: standalone)").addEventListener("change", () => {
  if (isStandalone() && installButton) installButton.hidden = true;
});

new MutationObserver(syncLabels).observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
window.addEventListener("online", () => announce("החיבור לאינטרנט חזר.", "Internet connection restored."));
window.addEventListener("offline", () => announce("האתר עבר למצב לא מקוון.", "The guide is now offline."));
window.addEventListener("resize", () => window.requestAnimationFrame(reportHorizontalOverflow));

async function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) return;
  if (!window.isSecureContext && !["localhost", "127.0.0.1"].includes(location.hostname)) return;

  const registration = await navigator.serviceWorker.register("./service-worker.js");
  document.documentElement.dataset.serviceWorker = registration.active?.state || "registered";
  document.documentElement.dataset.serviceWorkerControlled = String(Boolean(navigator.serviceWorker.controller));
  if (registration.waiting) showUpdate(registration.waiting);
  registration.addEventListener("updatefound", () => trackInstalling(registration));
  navigator.serviceWorker.addEventListener("controllerchange", () => {
    document.documentElement.dataset.serviceWorkerControlled = "true";
    if (!refreshApproved) return;
    refreshApproved = false;
    window.location.reload();
  });
}

syncLabels();
window.requestAnimationFrame(reportHorizontalOverflow);
window.setTimeout(reportHorizontalOverflow, 500);
if (isStandalone() && installButton) installButton.hidden = true;
registerServiceWorker().catch((error) => {
  console.error("Service Worker registration failed", error);
  announce("מצב Offline אינו זמין כרגע.", "Offline mode is currently unavailable.");
});
