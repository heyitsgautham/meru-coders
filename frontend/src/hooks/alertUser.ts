/** Default way the upload hooks report a rejected file or a failed action. */
export const alertUser = (message: string): void => {
  window.alert(message);
};
