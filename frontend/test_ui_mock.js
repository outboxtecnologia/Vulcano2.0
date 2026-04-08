const fetch = require('node-fetch');

(async () => {
    try {
        const res = await fetch('http://127.0.0.1:8000/api/receitas-caixa?empresa_id=1');
        const data = await res.json();
        const receitasData = data.dashboard_data || [];
        console.log("receitasData (API length):", receitasData.length);
        
        let filtered = receitasData;
        console.log("Filtered length:", filtered.length);
        
        const map = {};
        filtered.forEach(r => {
            const emp = r.empreendimento || "Sem Nome";
            if (!map[emp]) map[emp] = { unidades: [] };
            map[emp].unidades.push(r);
        });
        
        console.log("Aggregated length:", Object.keys(map).length);
    } catch (e) {
        console.error("Crash:", e);
    }
})();
