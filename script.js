async function cargarDatos() {
  const tabla = document.getElementById("tabla");
  const fecha = document.getElementById("fecha");

  tabla.innerHTML = `<tr><td colspan="9">Cargando datos...</td></tr>`;

  try {
    const resp = await fetch("datos_acciones.json?nocache=" + Date.now());
    if (!resp.ok) throw new Error("No existe datos_acciones.json todavía");

    const data = await resp.json();
    fecha.textContent = "Última actualización: " + (data.actualizado || "sin fecha");

    tabla.innerHTML = "";

    if (!data.resultados || data.resultados.length === 0) {
      tabla.innerHTML = `<tr><td colspan="9">No hay resultados todavía. Presiona "Ejecutar análisis en GitHub".</td></tr>`;
      return;
    }

    data.resultados.forEach(r => {
      const riesgo = String(r.Riesgo || "").toLowerCase();
      const senal = String(r.Senal || "");
      let claseSenal = "no";

      if (senal.includes("POSIBLE")) claseSenal = "compra";
      else if (senal.includes("VIGILAR")) claseSenal = "vigilar";

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${r.Accion}</strong></td>
        <td>${r["Precio actual"]}</td>
        <td>${r["Probabilidad tecnica"]}%</td>
        <td>${r["Entrada min"]} - ${r["Entrada max"]}</td>
        <td>${r["Stop loss"]}</td>
        <td>${r.Objetivo}</td>
        <td>${r.RSI}</td>
        <td><span class="badge ${riesgo}">${r.Riesgo}</span></td>
        <td class="${claseSenal}">${r.Senal}</td>
      `;

      tabla.appendChild(tr);
    });

  } catch (e) {
    fecha.textContent = "Sin datos";
    tabla.innerHTML = `<tr><td colspan="9">No se pudieron cargar datos. Presiona "Ejecutar análisis en GitHub".</td></tr>`;
  }
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
        body: JSON.stringify({
          ref: "main"
        })
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
