import { createRoot } from "react-dom/client";
import App from "./quote";

createRoot(document.getElementById("quote-root")).render(<App />);

export { App };
export default App;
