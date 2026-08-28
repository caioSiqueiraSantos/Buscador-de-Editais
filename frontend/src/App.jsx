// frontend/src/App.jsx
import { useEffect, useState } from 'react'

function App() {
  const [oportunidades, setOportunidades] = useState([])
  const [busca, setBusca] = useState("")

  useEffect(() => {
    fetch('http://localhost:8000/oportunidades')
      .then(response => response.json())
      .then(data => setOportunidades(data))
      .catch(error => console.error("Erro ao buscar dados:", error))
  }, [])

  const filtradas = oportunidades.filter(op =>
    op.titulo.toLowerCase().includes(busca.toLowerCase()) ||
    op.tematica.toLowerCase().includes(busca.toLowerCase())
  )

  const corAderencia = (nivel) => {
    switch (nivel?.toLowerCase()) {
      case 'alto': return 'bg-green-100 text-green-800 border-green-200'
      case 'médio': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'baixo': return 'bg-red-100 text-red-800 border-red-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  return (
    <div className="min-h-screen p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 border-b-4 border-blue-600 inline-block pb-2">
          Radar de Inovação - Metrô
        </h1>
        <p className="text-gray-600 mt-2">Buscador automatizado de editais e parcerias</p>
      </header>

      <div className="mb-6">
        <input
          type="text"
          placeholder="Buscar por título ou tema..."
          className="w-full max-w-md p-3 border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filtradas.map(op => (
          <div key={op.id} className="bg-white rounded-xl shadow-md p-6 border border-gray-100 hover:shadow-lg transition">
            <div className="flex justify-between items-start mb-4">
              <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">{op.categoria}</span>
              <span className={`text-xs px-2 py-1 rounded-full border font-semibold ${corAderencia(op.aderencia)}`}>
                Aderência: {op.aderencia}
              </span>
            </div>
            <h2 className="text-xl font-bold text-gray-800 mb-2">{op.titulo}</h2>
            <p className="text-sm text-gray-500 mb-4 font-medium">{op.instituicao} • Prazo: {op.prazo}</p>
            <p className="text-gray-700 text-sm mb-4 line-clamp-3">{op.resumo}</p>

            <div className="mt-auto">
              <div className="mb-4">
                <span className="text-xs font-semibold text-gray-500 block mb-1">Temática Relacionada:</span>
                <span className="text-sm bg-gray-100 px-2 py-1 rounded text-gray-700">{op.tematica}</span>
              </div>
              <a
                href={op.link}
                target="_blank"
                rel="noreferrer"
                className="block text-center w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition"
              >
                Ver Edital Completo
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default App