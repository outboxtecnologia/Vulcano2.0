import ast

scripts = [
    'update_app_shell.py',
    'refactor_receitas.py',
    'replace_script_vendas.py',
    'replace_script_receb.py',
]

def extract(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=filename)
    strings = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        strings[target.id] = node.value.value
    return strings

all_ex = {}
for s in scripts:
    all_ex.update(extract(s))

with open('conciliador_full.txt', 'r', encoding='utf-8') as f:
    concil = f.read()

# VulcanoViews
vulcano_header = """import React, { useState, useEffect, useMemo, useRef } from 'react';
import { 
    Download, RefreshCw, Upload, Play, CheckCircle2, ChevronDown, Layers, Activity,
    Database, TableProperties, Fingerprint, TrendingUp, Search, X, Maximize2, RotateCcw,
    Zap, Link as LinkIcon, Cpu, AlertCircle, FileText, CheckSquare, MessageSquare, Plus, PlusCircle, PenTool, Hash, Filter,
    LayoutGrid, History, ListFilter
} from 'lucide-react';
import {
  LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar,
  PieChart, Pie, Cell, Legend
} from 'recharts';
"""

vulcano = vulcano_header + "\n\n" + all_ex.get('receitas_view', '') + "\n\n" + all_ex.get('new_vendas_view', '') + "\n\n" + all_ex.get('new_recebimentos_view', '') + "\n\n" + concil

with open('frontend/src/VulcanoViews.jsx', 'w', encoding='utf-8') as f:
    f.write(vulcano)

# App
app_header = """import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom';
import SmartImporter from './SmartImporter';
import { DashboardMeta, VendasView, RecebimentosView, ConciliadorView } from './VulcanoViews';
import { EmpreendimentosView } from './EmpreendimentosView';
import './index.css';
import { 
  Building2, Database, TableProperties, Fingerprint, PieChart, Construction, 
  Users, Activity, ActivityIcon, BookUser, Globe2, Briefcase, Zap, Search, Bell, Download, Sun, Moon,
  Terminal, ShieldCheck, ShoppingCart, DollarSign, LayoutDashboard, ShieldAlert, Landmark
} from 'lucide-react';
import { Loader2, ArrowUpRight } from 'lucide-react';

const API_BASE = "http://127.0.0.1:8000";
"""

app_content = (
    app_header + "\n\n" +
    all_ex.get('new_navitem', '') + "\n\n" +
    "export default function App() {\n" +
    "  const [selectedEmpresa, setSelectedEmpresa] = useState('');\n" +
    "  const [empresaConfirmed, setEmpresaConfirmed] = useState(false);\n" +
    "  const [globalEmpresas, setGlobalEmpresas] = useState([]);\n" +
    "  const [empresasLoading, setEmpresasLoading] = useState(true);\n" +
    "  const [empresasError, setEmpresasError] = useState(null);\n" +
    "  const [currentView, setCurrentView] = useState('receitas');\n" +
    "  const [search, setSearch] = useState('');\n" +
    all_ex.get('new_theme', '') + "\n" +
    "  useEffect(() => {\n" +
    "    fetch(`${API_BASE}/api/vulcano/empresas`)\n" +
    "      .then(r => r.json())\n" +
    "      .then(d => { setGlobalEmpresas(d.data || []); setEmpresasLoading(false); })\n" +
    "      .catch(e => { console.error('Error fetching empresas:', e); setEmpresasError('Network Error contacting ERP node'); setEmpresasLoading(false); });\n" +
    "  }, []);\n\n" +
    "  const handleRunSQL = () => alert('SQL Execution triggered for environment: ' + selectedEmpresa);\n\n" +
    "  if (!empresaConfirmed) {\n" +
    all_ex.get('new_empresa_block', '') +
    "\n  }\n\n" +
    all_ex.get('new_shell', '') + "\n" +
    """
            {/* MAIN CONTENT AREA */}
            <main className="flex-1 overflow-x-hidden overflow-y-auto bg-surface-container-lowest/30 transition-colors p-8 relative">
              <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-primary/5 rounded-full blur-[120px] pointer-events-none -translate-y-1/2 translate-x-1/3"></div>
              <div className="max-w-[1920px] mx-auto min-h-full flex flex-col items-center">
                  <div className="w-full">
                      {currentView === 'empreendimentos' && <EmpreendimentosView />}
                      {currentView === 'vendas' && <VendasView selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'recebimentos' && <RecebimentosView selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'receitas' && <DashboardMeta selectedEmpresa={selectedEmpresa} />}
                      {currentView === 'conciliador' && <ConciliadorView />}
                      {currentView === 'importer' && <SmartImporter dbPath="poc_database.sqlite" />}
                      
                      {['clientes', 'explorer', 'tributos', 'poc', 'compare', 'fiscal', 'sero'].includes(currentView) && (
                          <div className="h-full flex flex-col items-center justify-center py-32 text-center relative z-10 w-full">
                              <div className="w-24 h-24 mb-10 rounded-sm bg-surface-container border border-outline-variant flex items-center justify-center animate-pulse">
                                  <Cpu size={40} className="text-primary/70" />
                              </div>
                              <h2 className="font-headline text-3xl font-bold tracking-widest text-on-surface uppercase mb-4">Módulo Indisponível</h2>
                              <p className="text-on-surface-variant font-light tracking-widest uppercase text-xs">O node solicitado está aguardando provisionamento de infraestrutura.</p>
                          </div>
                      )}
                  </div>
              </div>
            </main>
        </div>
    </div>
  );
}
"""
)

with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(app_content)

print("SUCCESS")
