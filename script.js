let datosGlobales = [];
let sectorActivo = "TODOS";

async function cargarDatos() {
  const tabla = document.getElementById("tabla");
  const fecha = document.getElementById("fecha");

  tabla.innerHTML = `<tr><td colspan="14">Cargando datos...</td></tr>`;

  try {
    const resp = await fetch("datos_acciones.json?nocache=" + Date.now());
    if (!resp.ok) throw new Error("No existe datos_acciones.json todavía");

    const data = await resp.json();
    fecha.textContent = "Última actualización: " + (data.actualizado || "sin fecha");

    datosGlobales = data.resultados || [];
    renderTabla();

  } catch (e) {
    fecha.textContent = "Sin datos";
    tabla.innerHTML = `<tr><td colspan="12">No se pudieron cargar datos. Presiona "Ejecutar análisis en GitHub".</td></tr>`;
  }
}

function filtrarSector(sector) {
  sectorActivo = sector;
  renderTabla();
}

function claseProbabilidad(prob) {
  if (prob >= 80) return "prob-verde";
  if (prob >= 65) return "prob-amarillo";
  return "prob-rojo";
}

function renderTabla() {
  const tabla = document.getElementById("tabla");
  const soloCompra = document.getElementById("soloCompra")?.checked || false;
  const soloHot = document.getElementById("soloHot")?.checked || false;

  let datos = [...datosGlobales];

  if (sectorActivo !== "TODOS") {
    datos = datos.filter(r => String(r.Sector || "").includes(sectorActivo));
  }

  if (soloCompra) {
    datos = datos.filter(r => String(r.Senal || "").includes("POSIBLE"));
  }

  if (soloHot) {
    datos = datos.filter(r => String(r["Hot Score"] || "").includes("🔥"));
  }

  datos.sort((a, b) => {
    const aCompra = String(a.Senal || "").includes("POSIBLE") ? 1 : 0;
    const bCompra = String(b.Senal || "").includes("POSIBLE") ? 1 : 0;

    const aRiesgo = ["BAJO", "MEDIO"].includes(a.Riesgo) ? 1 : 0;
    const bRiesgo = ["BAJO", "MEDIO"].includes(b.Riesgo) ? 1 : 0;

    const aHot = String(a["Hot Score"] || "").length;
    const bHot = String(b["Hot Score"] || "").length;

    const aProb = Number(a["Probabilidad tecnica"] || 0);
    const bProb = Number(b["Probabilidad tecnica"] || 0);

    return (bCompra - aCompra) || (bRiesgo - aRiesgo) || (bHot - aHot) || (bProb - aProb);
  });

  tabla.innerHTML = "";

  if (datos.length === 0) {
    tabla.innerHTML = `<tr><td colspan="12">No hay resultados con esos filtros.</td></tr>`;
    return;
  }

  datos.forEach(r => {
    const riesgo = String(r.Riesgo || "").toLowerCase();
    const senal = String(r.Senal || "");
    const prob = Number(r["Probabilidad tecnica"] || 0);
    const momentum = Number(r.Momentum || 0);

    let claseSenal = "no";
    if (senal.includes("POSIBLE")) claseSenal = "compra";
    else if (senal.includes("VIGILAR")) claseSenal = "vigilar";

    const claseMom = momentum >= 0 ? "mom-pos" : "mom-neg";

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${r.Accion}</strong></td>
      <td>${r.Sector || "Otro"}</td>
      <td>${r["Precio actual"]}</td>
      <td><span class="prob ${claseProbabilidad(prob)}">${prob}%</span></td>
      <td class="${claseMom}">${momentum}%</td>
      <td>${r["Hot Score"] || ""}</td>
      <td>${r["Entrada min"]} - ${r["Entrada max"]}</td>
      <td>${r["Stop loss"]}</td>
      <td>${r.Objetivo}</td>
      <td>${r.RSI}</td>
      <td><span class="badge ${riesgo}">${r.Riesgo}</span></td>
      <td class="${claseSenal}">${r.Senal}</td>
    `;

    tabla.appendChild(tr);
  });
}

async function ejecutarAnalisis() {
  const token = prompt("Pega tu token de GitHub:");

  if (!token) {
    alert("No pegaste el token.");
    return;
  }

  const usuario = "davascoj";
  const repo = "Analizador-acciones";
  const workflow = "analizar.yml";

  try {
    const respuesta = await fetch(
      `https://api.github.com/repos/${usuario}/${repo}/actions/workflows/${workflow}/dispatches`,
      {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Accept": "application/vnd.github+json",
          "X-GitHub-Api-Version": "2022-11-28"
        },
        body: JSON.stringify({ ref: "main" })
      }
    );

    if (respuesta.status === 204) {
      alert("Análisis enviado a GitHub. Espera 1 a 3 minutos y luego presiona Actualizar vista.");
    } else {
      const texto = await respuesta.text();
      alert("Error al ejecutar análisis: " + texto);
    }

  } catch (error) {
    alert("Error: " + error.message);
  }
}

cargarDatos();
