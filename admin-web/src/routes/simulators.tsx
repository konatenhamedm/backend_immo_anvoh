import React, { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import {
  Calculator,
  TrendingUp,
  Percent,
  PiggyBank,
  CheckCircle,
  Coins
} from 'lucide-react'
import { fetchApi } from '@/lib/api'
import { formatFCFA } from '@/lib/utils'

export const Route = createFileRoute('/simulators')({
  component: SimulatorsPage,
})

function SimulatorsPage() {
  const [purchasePrice, setPurchasePrice] = useState(66000000)
  const [downPayment, setDownPayment] = useState(15000000)
  const [durationYears, setDurationYears] = useState(15)
  const [monthlyRent, setMonthlyRent] = useState(450000)
  const [monthlyCharges, setMonthlyCharges] = useState(30000)

  const [simulationResult, setSimulationResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const data = await fetchApi<any>('/simulators/calculate-investment/', {
        method: 'POST',
        body: JSON.stringify({
          purchase_price: purchasePrice.toString(),
          down_payment: downPayment.toString(),
          annual_interest_rate: '7.5',
          loan_duration_years: durationYears,
          monthly_rent_estimated: monthlyRent.toString(),
          monthly_charges: monthlyCharges.toString(),
          tax_rate: '5.0',
          notary_fees_rate: '0.08',
        }),
      })
      setSimulationResult(data)
    } catch (err: any) {
      alert(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full space-y-6 animate-fade-in">
      {/* En-tête */}
      <div>
        <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
          Calculateur de Rentabilité Immobilière
          <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
            Écran 12
          </span>
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Simulateur financier Clean Architecture connecté en temps réel aux règles bancaires de Côte d'Ivoire.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Formulaire des paramètres */}
        <form
          onSubmit={handleSimulate}
          className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4"
        >
          <h2 className="text-sm font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider mb-2">
            Paramètres du Projet
          </h2>

          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
              Prix d'acquisition (FCFA)
            </label>
            <input
              type="number"
              value={purchasePrice}
              onChange={(e) => setPurchasePrice(Number(e.target.value))}
              className="w-full px-3.5 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:border-teal-500 focus:outline-hidden"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
              Apport personnel (FCFA)
            </label>
            <input
              type="number"
              value={downPayment}
              onChange={(e) => setDownPayment(Number(e.target.value))}
              className="w-full px-3.5 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:border-teal-500 focus:outline-hidden"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                Loyer mensuel (FCFA)
              </label>
              <input
                type="number"
                value={monthlyRent}
                onChange={(e) => setMonthlyRent(Number(e.target.value))}
                className="w-full px-3.5 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:border-teal-500 focus:outline-hidden"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                Durée du prêt (ans)
              </label>
              <input
                type="number"
                value={durationYears}
                onChange={(e) => setDurationYears(Number(e.target.value))}
                className="w-full px-3.5 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:border-teal-500 focus:outline-hidden"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
              Charges mensuelles (FCFA)
            </label>
            <input
              type="number"
              value={monthlyCharges}
              onChange={(e) => setMonthlyCharges(Number(e.target.value))}
              className="w-full px-3.5 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:border-teal-500 focus:outline-hidden"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 text-xs font-bold rounded-xl bg-teal-600 hover:bg-teal-700 text-white shadow-md shadow-teal-600/20 transition-all flex items-center justify-center gap-2 mt-4"
          >
            <Calculator className="w-4 h-4" />
            {loading ? 'Calcul en cours...' : 'Calculer la rentabilité & cash-flow'}
          </button>
        </form>

        {/* Résultats calculés */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs flex flex-col justify-between">
          <h2 className="text-sm font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider mb-4">
            Analyse Financière & Cash-flow
          </h2>

          {!simulationResult ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8 text-slate-400 text-xs italic">
              <Coins className="w-10 h-10 mb-2 opacity-50 text-teal-600" />
              Cliquez sur calculer pour obtenir la rentabilité brute/nette, la mensualité bancaire et le cash-flow estimé.
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60">
                  <span className="text-[11px] font-semibold text-emerald-800 dark:text-emerald-300">
                    Rentabilité Brute
                  </span>
                  <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1">
                    {simulationResult.gross_yield_percentage} %
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800/60">
                  <span className="text-[11px] font-semibold text-teal-800 dark:text-teal-300">
                    Rentabilité Nette
                  </span>
                  <div className="text-2xl font-black text-teal-600 dark:text-teal-400 mt-1">
                    {simulationResult.net_yield_percentage} %
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-500">Coût global projet (avec frais notaire) :</span>
                  <span className="font-bold text-slate-900 dark:text-white">
                    {formatFCFA(simulationResult.total_investment_cost)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Montant financé par la banque :</span>
                  <span className="font-bold text-slate-900 dark:text-white">
                    {formatFCFA(simulationResult.loan_amount)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Mensualité du prêt estimée :</span>
                  <span className="font-bold text-slate-900 dark:text-white">
                    {formatFCFA(simulationResult.monthly_loan_payment)} / mois
                  </span>
                </div>
                <div className="flex justify-between pt-2 border-t border-slate-200 dark:border-slate-700">
                  <span className="font-semibold text-slate-700 dark:text-slate-300">Cash-flow mensuel net :</span>
                  <span
                    className={`font-black ${
                      Number(simulationResult.monthly_cash_flow) >= 0
                        ? 'text-emerald-600 dark:text-emerald-400'
                        : 'text-rose-600 dark:text-rose-400'
                    }`}
                  >
                    {formatFCFA(simulationResult.monthly_cash_flow)} / mois
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
