/*
 * Funciones de apoyo que usan varias páginas. Se carga en base.html antes
 * que el JavaScript de cada página, así que todo lo de aquí ya existe
 * cuando ese código se ejecuta.
 */

/** Escapa texto para insertarlo dentro de HTML sin riesgo de XSS. */
function escaparHtml(texto) {
  return String(texto ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/** Lee una cookie por nombre (se usa para el token CSRF de Django). */
function obtenerCookie(nombre) {
  const prefijo = nombre + "=";
  for (const cookie of document.cookie.split(";")) {
    const limpia = cookie.trim();
    if (limpia.startsWith(prefijo)) {
      return decodeURIComponent(limpia.substring(prefijo.length));
    }
  }
  return null;
}

/**
 * Token CSRF para peticiones fetch. Primero lo busca en un
 * {% csrf_token %} de la página y, si no hay, en la cookie.
 */
function obtenerTokenCsrf() {
  const campo = document.querySelector("[name=csrfmiddlewaretoken]");
  return campo ? campo.value : obtenerCookie("csrftoken");
}

/**
 * Reemplaza el "0" de una URL generada con {% url 'nombre' 0 %} por el id
 * real. Ejemplo: "/secretaria/aprobar/0/" -> "/secretaria/aprobar/15/".
 */
function urlConId(urlBase, id) {
  return urlBase.replace("/0/", "/" + encodeURIComponent(id) + "/");
}

/**
 * Lee la respuesta JSON del servidor aunque el código HTTP sea de error
 * (400, 404, 409...), para poder mostrar el mensaje real, por ejemplo
 * "No hay cupos disponibles para la Experiencia Educativa con NRC 22222".
 * Si la respuesta no trae JSON (sesión expirada, error 500...), arma un
 * mensaje genérico.
 */
function leerRespuestaJson(response) {
  return response
    .json()
    .catch(() => ({}))
    .then((data) => {
      if (typeof data.success !== "boolean") {
        return {
          success: false,
          error:
            response.status === 403
              ? "Tu sesión expiró. Recarga la página e inicia sesión de nuevo."
              : `Ocurrió un error en el servidor (código ${response.status}).`,
        };
      }
      return data;
    });
}

/** Lee los datos que la plantilla dejó con el filtro |json_script. */
function leerJsonScript(id, valorPorDefecto = null) {
  const elemento = document.getElementById(id);
  if (!elemento) return valorPorDefecto;
  try {
    return JSON.parse(elemento.textContent);
  } catch (error) {
    console.error(`No se pudo leer el JSON de #${id}:`, error);
    return valorPorDefecto;
  }
}

/** Muestra u oculta un elemento usando la clase .oculto de base.css. */
function mostrarElemento(elemento, visible) {
  if (elemento) elemento.classList.toggle("oculto", !visible);
}
