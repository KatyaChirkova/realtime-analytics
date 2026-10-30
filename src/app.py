from __future__ import annotations

import math

import streamlit as st
import plotly.graph_objects as go

from analytics import (
    get_current_visitors,
    get_hourly_history,
    get_occupancy_history,
    get_occupancy_percent,
    get_peak_hour,
)
from config import settings

st.set_page_config(
    page_title="Мониторинг заполненности библиотеки",
    page_icon=None,
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {
        border: 1px solid #b8d9f2;
        border-radius: 10px;
        padding: 1.5rem 2rem 2rem 2rem;
        margin-top: 1rem;
    }
    .library-title {
        color: #2f6f9f;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 1.25rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="library-title">Мониторинг заполненности библиотеки</div>', unsafe_allow_html=True)

REFRESH_SECONDS = 5


def _nice_dtick(max_value: int) -> int:
    if max_value <= 5:
        return 1
    if max_value <= 20:
        return 2
    if max_value <= 50:
        return 5
    if max_value <= 100:
        return 10
    step = max(10, math.ceil(max_value / 8 / 10) * 10)
    return step


def build_history_chart(history):
    max_value = int(max(history["entries"].max(), history["exits"].max(), 0))
    dtick = _nice_dtick(max_value)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=history["hour"],
            y=history["entries"],
            mode="lines+markers",
            name="Входы",
            line=dict(width=2),
            marker=dict(size=5),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=history["hour"],
            y=history["exits"],
            mode="lines+markers",
            name="Выходы",
            line=dict(width=2),
            marker=dict(size=5),
        )
    )
    fig.update_layout(
        height=390,
        margin=dict(l=45, r=20, t=15, b=45),
        xaxis_title="Время",
        yaxis_title="Количество событий",
        hovermode="x unified",
        legend_title="Тип события",
        xaxis=dict(type="date", tickformat="%H:%M", nticks=9),
        yaxis=dict(rangemode="tozero", dtick=dtick, separatethousands=False),
    )
    return fig


def build_occupancy_chart(history):
    max_occupancy = int(max(history["occupancy"].max(), settings.library_capacity, 1))
    y_step = 20 if settings.library_capacity <= 120 else 25

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=history["hour"],
            y=history["occupancy"],
            mode="lines+markers",
            name="Посетители",
            line=dict(width=3),
            marker=dict(size=5),
            fill="tozeroy",
        )
    )
    fig.add_hline(
        y=settings.library_capacity,
        line_dash="dash",
        annotation_text=f"Вместимость: {settings.library_capacity}",
        annotation_position="top left",
    )
    fig.update_layout(
        height=390,
        margin=dict(l=45, r=20, t=15, b=45),
        xaxis_title="Время",
        yaxis_title="Количество посетителей",
        hovermode="x unified",
        xaxis=dict(type="date", tickformat="%H:%M", nticks=9),
        yaxis=dict(
            range=[0, max(settings.library_capacity, max_occupancy) * 1.08],
            dtick=y_step,
            rangemode="tozero",
            separatethousands=False,
        ),
        showlegend=False,
    )
    return fig


@st.fragment(run_every=REFRESH_SECONDS)
def realtime_panel() -> None:
    try:
        current = get_current_visitors()
        occupancy = get_occupancy_percent(settings.library_capacity)
        free = max(settings.library_capacity - current, 0)

        if occupancy >= 95:
            status = "🔴 Библиотека почти заполнена"
        elif occupancy >= 80:
            status = "🟠 Высокая загрузка"
        else:
            status = "🟢 Нормальная загрузка"

        c1, c2, c3 = st.columns(3)
        c1.metric("Посетителей сейчас", current)
        c2.metric("Заполненность", f"{occupancy:.1f}%")
        c3.metric("Свободно мест", free)
        st.info(status)

        history = get_hourly_history(24)
        st.subheader("Динамика входов и выходов за 24 часа")
        st.plotly_chart(build_history_chart(history), use_container_width=True)

        occupancy_history = get_occupancy_history(24)
        st.subheader("Заполненность библиотеки за 24 часа")
        st.plotly_chart(build_occupancy_chart(occupancy_history), use_container_width=True)

        peak_time, peak_entries = get_peak_hour(24)
        st.subheader("Пиковая активность")
        left, right = st.columns(2)
        with left:
            st.metric("Час с максимумом входов", peak_time)
        with right:
            st.metric("Количество входов за час", peak_entries)

        st.caption(f"Автообновление каждые {REFRESH_SECONDS} с")
    except Exception as exc:
        st.error(f"Не удалось получить данные из PostgreSQL: {exc}")
        st.info("Проверьте, что PostgreSQL запущен и параметры .env заполнены.")


realtime_panel()
