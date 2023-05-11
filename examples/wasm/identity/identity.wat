(module
  (type (;0;) (func (param i32) (result i32)))
  (func $id (type 0) (param i32) (result i32)
    local.get 0)
  (memory (;0;) 1)
  (export "memory" (memory 0))
  (export "id" (func $id)))
