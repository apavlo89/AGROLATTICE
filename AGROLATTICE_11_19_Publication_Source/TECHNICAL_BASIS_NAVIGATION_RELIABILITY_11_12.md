# AGROLATTICE 11.12 — Navigation reliability technical note

## Failure mode

Several command-centre pages keep a user-facing navigation widget with an
explicit Streamlit `key`. Streamlit persists that widget value in
`st.session_state`. Crop Decisions also kept a second mirror variable describing
the desired command-centre area.

A Priority button used to set only the mirror variable and call `st.rerun()`.
On the next run the radio widget's persisted key still contained `Overview`.
For keyed widgets, the persisted widget state takes precedence over the supplied
`index`; the widget therefore returned `Overview` again and wrote that back into
the mirror state. The requested route was effectively cancelled.

Attempting to set the radio widget's own key from the button handler is not a
safe general solution because the radio has already been instantiated earlier in
that Streamlit run.

## Two-phase route request

11.12 separates **requesting** navigation from **applying** navigation:

1. A button writes `target` to a dedicated non-widget request key.
2. It triggers a rerun.
3. At the top of the next render, before the navigation widget is instantiated,
   `consume_view_request()` removes the request and copies the target to the
   widget-owned key and optional mirror key.
4. The widget is then created with state already synchronized.

This respects Streamlit's widget/session-state lifecycle and prevents a stale
widget value from cancelling programmatic navigation.

## Scope

The helper is applied to:
- Crop Decision Command Centre priority-action routing;
- Persistent Twin command-centre shortcut buttons;
- Climate & Earth Observation's EO shortcut.

No application data, model artifacts or database records are modified by this
routing helper.
