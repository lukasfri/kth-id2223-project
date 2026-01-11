import './App.css'
import { MapComponent } from './mapComponent'
import {QueryClient, QueryClientProvider} from "@tanstack/react-query";

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            retry: false
        }
    }
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <h1>Vite + React</h1>
      <MapComponent />
    </QueryClientProvider>
  )
}

export default App
