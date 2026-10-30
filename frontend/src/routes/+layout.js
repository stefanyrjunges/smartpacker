// This app runs in the browser using localStorage and fetch,
// so we turn off server side rendering and build it as a single page app. The application will render in the browser entirely. The server doesn't have access to the user's browser localStorage so it'd throw an error
export const ssr = false;
