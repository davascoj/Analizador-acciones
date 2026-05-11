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
      tabla.innerHTML = `<tr><td colspan="9">No hay resultados todavía. Ejecuta el BAT para activar GitHub Actions.</td></tr>`;
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
    tabla.innerHTML = `<tr><td colspan="9">No se pudieron cargar datos. Primero ejecuta el BAT para activar el análisis en GitHub.</td></tr>`;
  }
}

cargarDatos();
