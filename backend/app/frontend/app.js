const feedbackBox = document.getElementById("feedback");
const lightsTableBody = document.getElementById("lights-table-body");
const musicList = document.getElementById("music-list");
const lightForm = document.getElementById("light-form");
const musicForm = document.getElementById("music-form");
let lightsSocket;
const lightsState = new Map();

const apiClient = async (url, options = {}) => {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: response.statusText }));
    const errorMessage = detail?.detail || "Đã xảy ra lỗi";
    throw new Error(errorMessage);
  }
  return response.json();
};

const showFeedback = (message, isError = false) => {
  feedbackBox.textContent = message;
  feedbackBox.classList.toggle("visible", Boolean(message));
  feedbackBox.classList.toggle("error", isError);
};

const renderLightsTable = () => {
  const lights = Array.from(lightsState.values()).sort((a, b) =>
    a.location.localeCompare(b.location, "vi", { sensitivity: "base" }),
  );
  if (!lights.length) {
    lightsTableBody.innerHTML = `<tr><td colspan="2">Chưa có dữ liệu</td></tr>`;
    return;
  }
  lightsTableBody.innerHTML = lights
    .map(
      (light) => `
        <tr>
          <td>${light.location}</td>
          <td>${light.is_on ? "Bật" : "Tắt"}</td>
        </tr>
      `,
    )
    .join("");
};

const applyLightSnapshot = (lights) => {
  lightsState.clear();
  lights.forEach((light) => {
    if (!light?.location) return;
    const key = light.location.toLowerCase().trim();
    lightsState.set(key, {
      location: light.location,
      is_on: Boolean(light.is_on),
    });
  });
  renderLightsTable();
};

const applyLightUpdate = (light) => {
  if (!light?.location) return;
  const key = light.location.toLowerCase().trim();
  lightsState.set(key, {
    location: light.location,
    is_on: Boolean(light.is_on),
  });
  renderLightsTable();
};

const updateMusicList = (library) => {
  if (!library.length) {
    musicList.innerHTML = `<li>Thư viện trống</li>`;
    return;
  }
  musicList.innerHTML = library.map((song) => `<li>${song}</li>`).join("");
};

const refreshLights = async () => {
  try {
    const lights = await apiClient("/smart-home/lights");
    applyLightSnapshot(lights);
  } catch (error) {
    showFeedback(error.message, true);
  }
};

const refreshMusicLibrary = async () => {
  try {
    const library = await apiClient("/smart-home/music/library");
    updateMusicList(library);
  } catch (error) {
    showFeedback(error.message, true);
  }
};

lightForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const submitter = event.submitter;
  const action = submitter?.dataset?.action;
  if (!action) {
    return;
  }
  const formData = new FormData(lightForm);
  const location = formData.get("location");
  if (!location) {
    showFeedback("Vui lòng nhập vị trí đèn", true);
    return;
  }

  try {
    const endpoint = action === "on" ? "/smart-home/lights/on" : "/smart-home/lights/off";
    const state = await apiClient(endpoint, {
      method: "POST",
      body: JSON.stringify({ location }),
    });
    showFeedback(`Đèn tại "${state.location}" hiện đang ${state.is_on ? "bật" : "tắt"}.`);
    await refreshLights();
  } catch (error) {
    showFeedback(error.message, true);
  }
});

musicForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(musicForm);
  const title = formData.get("title");
  if (!title) {
    showFeedback("Vui lòng nhập tên bài hát", true);
    return;
  }

  try {
    const result = await apiClient("/smart-home/music/play", {
      method: "POST",
      body: JSON.stringify({ title }),
    });
    showFeedback(`Đang phát bài: ${result.selected_song}`);
  } catch (error) {
    showFeedback(error.message, true);
  }
});

const setupLightsStream = () => {
  try {
    if (lightsSocket) {
      return;
    }
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(
      `${protocol}://${window.location.host}/smart-home/lights/stream`,
    );
    lightsSocket = socket;

    socket.addEventListener("message", (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === "snapshot" && Array.isArray(payload.lights)) {
          applyLightSnapshot(payload.lights);
        } else if (payload.type === "update" && payload.light) {
          applyLightUpdate(payload.light);
        }
      } catch (error) {
        console.error("Không thể phân tích dữ liệu websocket", error);
      }
    });

    socket.addEventListener("close", () => {
      if (lightsSocket === socket) {
        lightsSocket = undefined;
        setTimeout(setupLightsStream, 3000);
      }
    });

    socket.addEventListener("error", () => {
      socket.close();
    });
  } catch (error) {
    console.error("Không thể kết nối websocket", error);
  }
};

refreshLights();
refreshMusicLibrary();
setupLightsStream();
