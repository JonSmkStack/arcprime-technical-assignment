import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { DisclosureDetailPage } from "./pages/DisclosureDetailPage";
import { DisclosuresPage } from "./pages/DisclosuresPage";
import { UploadPage } from "./pages/UploadPage";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<UploadPage />} />
        <Route path="disclosures" element={<DisclosuresPage />} />
        <Route path="disclosures/:id" element={<DisclosureDetailPage />} />
      </Route>
    </Routes>
  );
}

export default App;
