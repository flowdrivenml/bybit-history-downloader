# NORMALIZATION_RULES = {
#     "OKX-T1": [
#         Rule(
#             source="created_time",
#             target="timestamp",
#             kind="map",
#             transform="milliseconds_to_nanoseconds",
#         ),
#         Rule(
#             source="trade_id",
#             target="trade_id",
#             kind="map",
#         ),
#         Rule(
#             source="source",
#             target="is_rpi",
#             kind="map",
#         ),
#     ],
#
#     "GATE-B2": [
#         Rule(
#             source="signed_size",
#             target="side",
#             kind="derive",
#             transform="sign_to_book_side",
#         ),
#         Rule(
#             source="make",
#             target="operation",
#             kind="derive",
#             transform="add",
#         ),
#         Rule(
#             source="take",
#             target="operation",
#             kind="derive",
#             transform="subtract",
#         ),
#     ],
# }
