# CP material schemas

These are local cp-work schemas, version 2.0.0, derived from MiMeDat revision
8c85283feee8301cd9b23bd837ec446603435ec3. They are no longer unmodified upstream
copies. JSON Schema Draft 2019-09 applies to JSON and safely loaded YAML alike.
The material wrapper references the CP schema locally; no remote schema retrieval
is needed. Register local file URIs when validating with Python jsonschema.

## Model selection

Set `constitutive_model.plastic_model_name` to exactly `ICAMS CP-UMAT` or
`DAMASK phenopowerlaw`. Mutually exclusive `oneOf` branches validate parameters.
DAMASK isotropic and kinehardening are not supported. The CP schema is standalone:
it does not inherit the old mandatory scalar hardening requirements.

Both models use descriptive common keys: `number_slip_systems`,
`reference_shear_rate`, `stress_exponent`, and
`initial_critical_resolved_shear_stress`. The old
`strain_rate_sensitivity_exponent` is rejected. The stress exponent is n in the
power law, not sensitivity m=1/n. Existing entries need an explicit model name,
the renamed exponent where applicable, and Time units; no data migration is done.

ICAMS accepts scalar or family-array parameters. `flag_isotropic_hardening` is
required explicitly: 0 permits omitting its hardening parameters; 1 requires
saturated_slip_resistance, reference_hardening_rate, hardening_exponent,
self_hardening, and cross_hardening. Other active blocks still need semantic
validation by the forthcoming exporter, including packed-flag consistency.

DAMASK requires family arrays. Common-key export aliases are:
number_slip_systems -> N_sl; reference_shear_rate -> dot_gamma_0_sl;
stress_exponent -> n_sl; initial_critical_resolved_shear_stress -> xi_0_sl;
saturated_slip_resistance -> xi_inf_sl; reference_hardening_rate -> h_0_sl-sl;
hardening_exponent -> a_sl. Interaction and twin parameters retain DAMASK names.
Hardening fields remain required by this reader; zero reference_hardening_rate
represents disabled slip hardening. Positive twin counts activate twin requirements.
This schema targets slip-containing phenopowerlaw; twin-only configurations are
not currently represented by the common required slip fields.

Units are actual validated properties: Stress and Stiffness are Pa or MPa for
ICAMS and Pa for DAMASK, and Time must be s. Exporters must convert declared units,
not simply relabel them. DAMASK entries require lattice (cF/cI/hP/tI); ICAMS entries
require material_id and space_group_number. Metadata may retain additional fields.

The schema checks structure, types, allowed flags, and selected requirements.
Python checks must additionally enforce family-array lengths, family ordering,
nonzero active slip counts, lattice-specific interactions and c/a requirements,
finite values, and constitutive compatibility. Unknown plastic/elastic keys are
rejected. Numerical and physical equivalence between the implementations is not
implied by these aliases. The database is not directly a DAMASK material.yaml;
an exporter must assemble phase/mechanical and the other configuration sections.
