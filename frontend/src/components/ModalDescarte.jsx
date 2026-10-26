import { useState } from 'react'

export default function ModalDescarte({ isOpen, onClose, edital, onDescartar }) {
  const [motivoSelecionado, setMotivoSelecionado] = useState('Fora do escopo de mobilidade sobre trilhos')
  const [motivoCustom, setMotivoCustom] = useState('')
  const [salvando, setSalvando] = useState(false)

  if (!isOpen || !edital) return null

  const opcoesRapidas = [
    'Fora do escopo de mobilidade sobre trilhos',
    'Falso positivo (transporte rodoviário ou agronegócio)',
    'Incompatível com objetivos estratégicos do Metrô',
    'Prazo de submissão inviável ou vencido',
    'Outro motivo personalizado'
  ]

  const handleConfirmar = async () => {
    const motivoFinal = motivoSelecionado === 'Outro motivo personalizado'
      ? (motivoCustom.trim() || 'Falso positivo descartado pelo especialista')
      : (motivoCustom.trim() ? `${motivoSelecionado} - ${motivoCustom.trim()}` : motivoSelecionado)

    try {
      setSalvando(true)
      await onDescartar(edital.id, motivoFinal)
      onClose()
    } catch (err) {
      console.error('Erro ao descartar edital:', err)
    } finally {
      setSalvando(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-700 rounded-3xl w-full max-w-xl shadow-2xl shadow-rose-950/20 overflow-hidden">
        
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-start justify-between gap-4 bg-slate-900/90">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 shrink-0">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Descartar Edital & Calibrar IA</h2>
              <p className="text-xs text-slate-400">Treine a IA para evitar falsos positivos semelhantes no futuro</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 p-2 rounded-full transition-colors cursor-pointer"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5 text-sm">
          <div className="bg-slate-950/60 p-4 rounded-2xl border border-slate-800">
            <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block mb-1">Edital selecionado</span>
            <p className="text-slate-200 font-semibold leading-snug line-clamp-2">{edital.titulo}</p>
          </div>

          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-slate-300 block mb-2.5">
              Por que este edital não é aderente? (Opções Rápidas)
            </label>
            <div className="space-y-2">
              {opcoesRapidas.map((opcao) => (
                <button
                  key={opcao}
                  type="button"
                  onClick={() => setMotivoSelecionado(opcao)}
                  className={`w-full text-left px-4 py-2.5 rounded-xl border text-xs transition-all cursor-pointer flex items-center justify-between ${
                    motivoSelecionado === opcao
                      ? 'bg-rose-500/15 border-rose-500/50 text-rose-300 font-semibold shadow-sm'
                      : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                  }`}
                >
                  <span>{opcao}</span>
                  {motivoSelecionado === opcao && (
                    <span className="w-2 h-2 rounded-full bg-rose-400 shrink-0"></span>
                  )}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-xs font-medium text-slate-400 block mb-1.5">
              Justificativa complementar (opcional):
            </label>
            <textarea
              rows="2"
              placeholder="Ex: Focado exclusivamente em caminhões de carga agrícola, sem aplicação em vias ou estações metroviárias..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 focus:outline-none focus:border-rose-500/60 transition-all placeholder:text-slate-600 resize-none"
              value={motivoCustom}
              onChange={(e) => setMotivoCustom(e.target.value)}
            />
          </div>

          <div className="bg-cyan-950/20 border border-cyan-800/30 p-3 rounded-xl flex items-start gap-2.5 text-xs text-cyan-300/90">
            <svg className="w-4 h-4 shrink-0 mt-0.5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>
              <strong>Aprendizado Ativo:</strong> Esta ação remove o edital da listagem ativa e envia a justificativa diretamente para o prompt do Gemini como exemplo negativo nos próximos rastreamentos.
            </span>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-900/90 border-t border-slate-800 flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={salvando}
            className="px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 transition-colors cursor-pointer"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={handleConfirmar}
            disabled={salvando}
            className="px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-rose-600 hover:bg-rose-500 transition-all shadow-lg shadow-rose-950/40 cursor-pointer flex items-center gap-2"
          >
            {salvando ? (
              <span>Gravando aprendizado...</span>
            ) : (
              <>
                <span>Descartar e Treinar IA</span>
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </>
            )}
          </button>
        </div>

      </div>
    </div>
  )
}
