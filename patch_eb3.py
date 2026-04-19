import sys

with open('frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    code = f.read()

eb_class = """
class TabelaErrorBoundary extends React.Component {
  constructor(props) { super(props); this.state = { hasError: false, error: null, info: null }; }
  static getDerivedStateFromError(error) { return { hasError: true, error }; }
  componentDidCatch(error, info) { this.setState({ info }); console.error("TABELA CRASHED", error, info); }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '40px', background: 'red', border: '5px solid yellow', color: 'white', zIndex: 999999, position: 'relative', width: '100%', height: '100%', overflow: 'auto' }}>
           <h2 style={{ fontSize: '24px', fontWeight: 'bold' }}>CRASH DETECTADO NA TABELA MAPA! POR FAVOR, ENVIE O TEXTO ABAIXO PRO DEV:</h2>
           <p style={{ fontFamily: 'monospace', fontSize: '18px', margin: '20px 0', background: '#000', padding: '10px' }}>{this.state.error?.toString()}</p>
           <pre style={{ fontSize: '12px', background: '#330000', padding: '10px' }}>{this.state.info?.componentStack}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}
"""

if "class TabelaErrorBoundary" not in code:
    code = code.replace(
        "function TabelaMapaComparativa({",
        eb_class + "\nfunction TabelaMapaComparativa({"
    )

code = code.replace(
    '<TabelaMapaComparativa questor={questorManual} vulcano1={vulcano1} vulcano2={vulcano2} dashboardMeta={dashboardMeta} />',
    '<TabelaErrorBoundary><TabelaMapaComparativa questor={questorManual} vulcano1={vulcano1} vulcano2={vulcano2} dashboardMeta={dashboardMeta} /></TabelaErrorBoundary>'
)

with open('frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
    f.write(code)

print("Error boundary securely injected.")
