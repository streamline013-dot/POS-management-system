/* Print Shop POS — app configuration (v39)
 * ----------------------------------------------------------------------------
 * Fill this in once, commit it, and deploy. Every device that opens the app gets it.
 *
 * Leave "firebase.apiKey" empty to run in LOCAL MODE: no login, data stays on one
 * device (like v38). Fill in the Firebase values to turn on Google sign-in, roles
 * (developer / admin / staff), and realtime sync on every device.
 *
 * Is it safe to commit these values? Yes. A Firebase web config is not a password:
 * it only says which Firebase project to talk to. Your data is protected by the
 * database rules (generated in Developer Console → Integrations) and by sign-in.
 * Never put a Gemini API key, a password, or a service-account key in this file.
 *
 * Step-by-step: 03_SETUP_GUIDES/03_Firebase_Setup.md and 06_Environment_Variables.md (configuration reference)
 */
window.POS_CONFIG = {
  /* From Firebase Console → Project settings → General → Your apps → Web app → "firebaseConfig".
     databaseURL is shown at the top of Build → Realtime Database. */
  firebase: {
    apiKey: "",
    authDomain: "",
    databaseURL: "",
    projectId: "",
    appId: "",
    storageBucket: "",
    messagingSenderId: ""
  },

  /* Google accounts (Gmail) that are DEVELOPERS: full access + Developer Console.
     Developers sign in through the Developer portal (your-site/?portal=developer) with
     Google AND a Developer PIN they create on first sign-in. Use lowercase.
     After changing this list, copy the new rules from
     Developer Console → Integrations → Database rules and Publish them in Firebase. */
  developers: [
    "your.email@gmail.com"
  ],

  /* One deployment = one shop. Letters, numbers, - and _ only. Changing it later
     starts a new, empty shop in the database (the old one is kept). */
  shopId: "main",

  /* Optional: Google Drive backup. The "Web client ID" of the Firebase Google sign-in
     (ends in .apps.googleusercontent.com). The developer can also set it later in
     Developer Console → Integrations, which overrides this value. */
  googleDriveClientId: "",

  /* Firebase JavaScript SDK version loaded from gstatic.com. Change only if told to
     by the troubleshooting guide (v38 used "10.14.1"). */
  firebaseSdkVersion: "13.4.0",

  /* Name shown on the sign-in screen before the shop name has loaded. */
  appName: "Print Shop POS"
};
