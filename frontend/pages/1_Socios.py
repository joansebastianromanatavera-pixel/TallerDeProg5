"""Members management page (CRUD against the GymFlow API)."""

from typing import Any

import pandas as pd
import streamlit as st

import api_client

st.set_page_config(page_title="Socios · GymFlow", page_icon="👥", layout="wide")
st.title("👥 Socios")

COLUMNS = {
    "id": "ID",
    "name": "Nombre",
    "email": "Email",
    "phone": "Teléfono",
    "registered_at": "Fecha de registro",
    "active": "Activo",
}


def flash(message: str) -> None:
    """Keep a success message across st.rerun()."""
    st.session_state["flash"] = message


if message := st.session_state.pop("flash", None):
    st.success(message)

try:
    members: list[dict[str, Any]] = api_client.list_members()
except api_client.APIError as exc:
    st.error(str(exc))
    st.stop()

# ---------- Table ----------
st.subheader("Listado")
if members:
    df = pd.DataFrame(members)[list(COLUMNS)].rename(columns=COLUMNS)
    st.dataframe(df, hide_index=True, width="stretch")
else:
    st.info("Aún no hay socios registrados.")

tab_create, tab_edit, tab_delete = st.tabs(["➕ Crear", "✏️ Editar", "🗑️ Eliminar"])

# ---------- Create ----------
with tab_create:
    with st.form("create_member", clear_on_submit=True):
        name = st.text_input("Nombre *")
        email = st.text_input("Email *")
        phone = st.text_input("Teléfono")
        active = st.checkbox("Activo", value=True)
        if st.form_submit_button("Crear socio", type="primary"):
            try:
                created = api_client.create_member(
                    {"name": name, "email": email, "phone": phone or None, "active": active}
                )
                flash(f"Socio '{created['name']}' creado con id {created['id']}.")
                st.rerun()
            except api_client.APIError as exc:
                st.error(str(exc))


def member_label(member: dict[str, Any]) -> str:
    return f"#{member['id']} · {member['name']} ({member['email']})"


# ---------- Edit ----------
with tab_edit:
    if not members:
        st.info("No hay socios para editar.")
    else:
        selected = st.selectbox("Socio a editar", members, format_func=member_label, key="edit_select")
        with st.form(f"edit_member_{selected['id']}"):
            name = st.text_input("Nombre", value=selected["name"])
            email = st.text_input("Email", value=selected["email"])
            phone = st.text_input("Teléfono", value=selected.get("phone") or "")
            active = st.checkbox("Activo", value=selected["active"])
            if st.form_submit_button("Guardar cambios", type="primary"):
                try:
                    api_client.update_member(
                        selected["id"],
                        {"name": name, "email": email, "phone": phone or None, "active": active},
                    )
                    flash(f"Socio #{selected['id']} actualizado.")
                    st.rerun()
                except api_client.APIError as exc:
                    st.error(str(exc))

# ---------- Delete ----------
with tab_delete:
    if not members:
        st.info("No hay socios para eliminar.")
    else:
        selected = st.selectbox("Socio a eliminar", members, format_func=member_label, key="delete_select")
        st.warning("Se eliminarán también sus membresías y rutinas. Esta acción no se puede deshacer.")
        confirm = st.checkbox(f"Confirmo que quiero eliminar a {selected['name']}", key=f"confirm_{selected['id']}")
        if st.button("Eliminar socio", type="primary", disabled=not confirm):
            try:
                api_client.delete_member(selected["id"])
                flash(f"Socio '{selected['name']}' eliminado.")
                st.rerun()
            except api_client.APIError as exc:
                st.error(str(exc))
