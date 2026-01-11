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
      <div className='w-screen h-screen'>
      <MapComponent />

      </div>
    </QueryClientProvider>
  )
}

export default App
