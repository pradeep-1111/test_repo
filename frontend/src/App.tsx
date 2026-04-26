import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { ReviewDetail } from "./pages/ReviewDetail";
import { ManualReview } from "./pages/ManualReview";
import { Jobs } from "./pages/Jobs";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: "reviews/:reviewId", element: <ReviewDetail /> },
      { path: "manual-review", element: <ManualReview /> },
      { path: "jobs", element: <Jobs /> },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}