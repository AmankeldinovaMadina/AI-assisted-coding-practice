# CAL-101: Submission sometimes returns another employee's request

**Type:** bug · **Priority:** high

## Report

Two employees submitted unrelated meetings through the internal client. The second employee received a response containing the first employee's request ID and organization. Both clients generate retry tokens locally and may generate the same token.

Retries from one employee appear to work. Please investigate without disabling idempotency or trusting caller-provided organization data.

## Reproduction notes from support

- Directory contains employees `e-101` in Research and `e-202` in Sales.
- Each submits a valid meeting with idempotency key `client-token-1`.
- The second response unexpectedly contains `employee_id == "e-101"`.

## Acceptance criteria

- Different employees can reuse a token and still create distinct stored requests.
- Repeating a valid submission for the same employee and token returns the original record and creates no duplicate, including after a batch has finalized it.
- Keep existing validation and the public service API.
- Add focused regression coverage and explain why the current implementation fails.

The report concerns sequential requests in the supported single-worker deployment. Distributed race handling is outside scope.
