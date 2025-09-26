import { BrowserRouter, Route, Routes } from "react-router-dom";
import Home from "./Home";
import GlobalContextProvider from "./Context/GlobalContext";

function App() {
  return (
    <>
      <GlobalContextProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="*" element={<div>Not Found</div>} />
          </Routes>
        </BrowserRouter>
      </GlobalContextProvider>
    </>
  );
}

export default App;
