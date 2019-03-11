Purchase module doesn't depend on stock now. This module depends on stock,
if you need to use it without the stock module you can make a PR to
split the module (mainly displaying qty_available of a product)

The module uses Form emulation from backend.
Once onchange_helper is stabilized, we should switch to it
because it is more robust and has better perfs.
