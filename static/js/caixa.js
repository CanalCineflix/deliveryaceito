document.addEventListener('DOMContentLoaded', () => {

    // 1. FUNÇÕES PARA GERENCIAR MODAIS
    window.showModal = (modalId) => {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            document.body.style.overflow = 'hidden'; // Evita scroll no fundo
        }
    };

    window.hideModal = (modalId) => {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            document.body.style.overflow = 'auto'; // Restaura o scroll
        }
    };

    // 2. LÓGICA DO FORMULÁRIO "NOVO PEDIDO DE BALCÃO"
    const productSearchInput = document.getElementById('product-search');
    const searchResultsList = document.getElementById('product-search-results');
    const orderItemsList = document.getElementById('order-items-list');
    const orderTotalPriceSpan = document.getElementById('order-total-price');
    const paymentMethodSelect = document.getElementById('payment-method');
    const changeInputGroup = document.getElementById('change-input-group');
    const changeForInput = document.getElementById('change-for');
    const changeAmountSpan = document.getElementById('change-amount');
    const counterOrderForm = document.getElementById('counter-order-form');

    // Mapeamento de produtos no carrinho
    const cart = new Map();

    const updateCartDisplay = () => {
        orderItemsList.innerHTML = '';
        let totalPrice = 0;
        cart.forEach((item, productId) => {
            const listItem = document.createElement('li');
            listItem.className = 'flex justify-between items-start py-2 border-b last:border-b-0';
            listItem.innerHTML = `
                <div class="flex-1">
                    <div class="flex items-center">
                        <button type="button" class="text-danger hover:text-danger/70 mr-2" onclick="changeQuantity('${productId}', -1)">
                            <i data-lucide="minus-circle" class="w-5 h-5"></i>
                        </button>
                        <span class="font-bold text-lg">${item.quantity}</span>
                        <button type="button" class="text-success hover:text-success/70 ml-2" onclick="changeQuantity('${productId}', 1)">
                            <i data-lucide="plus-circle" class="w-5 h-5"></i>
                        </button>
                        <span class="ml-4 font-medium">${item.name}</span>
                    </div>
                    <textarea data-product-id="${productId}" class="mt-2 w-full text-sm p-1 border rounded" placeholder="Observação do item...">${item.notes || ''}</textarea>
                </div>
                <div class="text-right">
                    <span class="font-bold">R$ ${(item.quantity * item.price).toFixed(2)}</span>
                    <button type="button" class="ml-2 text-danger hover:text-danger/70" onclick="removeItem('${productId}')">
                        <i data-lucide="trash-2" class="w-4 h-4"></i>
                    </button>
                </div>
            `;
            orderItemsList.appendChild(listItem);
            totalPrice += item.quantity * item.price;
        });

        orderTotalPriceSpan.textContent = `R$ ${totalPrice.toFixed(2)}`;
        updateChange();
        // Atualiza ícones Lucide
        lucide.createIcons();
    };

    // Funções para manipular o carrinho
    window.changeQuantity = (productId, change) => {
        const item = cart.get(productId);
        if (item) {
            item.quantity += change;
            if (item.quantity <= 0) {
                cart.delete(productId);
            }
            updateCartDisplay();
        }
    };

    window.removeItem = (productId) => {
        cart.delete(productId);
        updateCartDisplay();
    };

    const updateChange = () => {
        const totalPrice = parseFloat(orderTotalPriceSpan.textContent.replace('R$', ''));
        const changeFor = parseFloat(changeForInput.value.replace(',', '.')) || 0;
        const changeAmount = changeFor - totalPrice;
        changeAmountSpan.textContent = `R$ ${changeAmount > 0 ? changeAmount.toFixed(2) : '0.00'}`;
    };

    const toggleChangeInput = () => {
        if (paymentMethodSelect.value === 'dinheiro') {
            changeInputGroup.classList.remove('hidden');
            changeForInput.setAttribute('required', 'required');
        } else {
            changeInputGroup.classList.add('hidden');
            changeForInput.removeAttribute('required');
            changeForInput.value = '';
            updateChange();
        }
    };

    // Event Listeners para o formulário de Novo Pedido
    if (productSearchInput) {
        productSearchInput.addEventListener('input', async () => {
            const query = productSearchInput.value;
            if (query.length > 2) {
                const response = await fetch(`/caixa/buscar_produtos?q=${query}`);
                const products = await response.json();
                searchResultsList.innerHTML = '';
                if (products.length > 0) {
                    products.forEach(product => {
                        const li = document.createElement('li');
                        li.className = 'p-2 cursor-pointer hover:bg-gray-100 rounded';
                        li.textContent = `${product.name} (R$ ${product.price.toFixed(2)})`;
                        li.dataset.id = product.id;
                        li.dataset.name = product.name;
                        li.dataset.price = product.price;
                        searchResultsList.appendChild(li);
                    });
                    searchResultsList.classList.remove('hidden');
                } else {
                    searchResultsList.classList.add('hidden');
                }
            } else {
                searchResultsList.classList.add('hidden');
            }
        });
    }
    
    if (searchResultsList) {
        searchResultsList.addEventListener('click', (e) => {
            const li = e.target.closest('li');
            if (li) {
                const productId = li.dataset.id;
                const productName = li.dataset.name;
                const productPrice = parseFloat(li.dataset.price);

                if (cart.has(productId)) {
                    const item = cart.get(productId);
                    item.quantity += 1;
                } else {
                    cart.set(productId, {
                        name: productName,
                        price: productPrice,
                        quantity: 1,
                        notes: ''
                    });
                }
                updateCartDisplay();
                searchResultsList.classList.add('hidden');
                productSearchInput.value = '';
            }
        });
    }

    if (orderItemsList) {
        orderItemsList.addEventListener('input', (e) => {
            if (e.target.tagName === 'TEXTAREA') {
                const productId = e.target.dataset.productId;
                if (cart.has(productId)) {
                    cart.get(productId).notes = e.target.value;
                }
            }
        });
    }

    if (paymentMethodSelect) {
        paymentMethodSelect.addEventListener('change', toggleChangeInput);
    }
    if (changeForInput) {
        changeForInput.addEventListener('input', updateChange);
    }

    if (counterOrderForm) {
        counterOrderForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const notes = document.getElementById('order-notes').value;
            const paymentMethod = paymentMethodSelect.value;
            const changeFor = changeForInput.value.replace(',', '.');
            
            if (cart.size === 0) {
                alert('Adicione pelo menos um item ao pedido.');
                return;
            }

            const items = Array.from(cart).map(([productId, item]) => ({
                product_id: productId,
                quantity: item.quantity,
                notes: item.notes
            }));

            const data = {
                items,
                payment_method: paymentMethod,
                change_for: changeFor,
                notes
            };

            try {
                const response = await fetch('/caixa/finalize_counter_order', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                const result = await response.json();
                if (result.success) {
                    alert('Venda registrada com sucesso!');
                    window.location.reload();
                } else {
                    alert('Erro: ' + result.message);
                }
            } catch (error) {
                console.error('Erro ao finalizar pedido:', error);
                alert('Ocorreu um erro ao finalizar o pedido.');
            }
        });
    }

    // 3. ATALHOS DE TECLADO
    document.addEventListener('keydown', (e) => {
        if (e.key === 'F2') {
            e.preventDefault();
            const cashStatusCard = document.getElementById('cash-status-card');
            if (cashStatusCard && cashStatusCard.classList.contains('bg-green-100')) {
                showModal('new-order-modal');
                productSearchInput.focus();
                toggleChangeInput(); 
            }
        }
    });

    // 4. FUNÇÃO PARA EXIBIR A COMANDA DE IMPRESSÃO
    const displayReceiptModal = (orderId, receiptHtml) => {
        document.getElementById('print-order-id').textContent = orderId;
        document.getElementById('print-content').innerHTML = receiptHtml;
        showModal('print-modal');
    };

    // 5. FUNÇÃO PARA IMPRIMIR
    window.printReceipt = () => {
        const printContent = document.getElementById('print-content').innerHTML;
        const newWindow = window.open('', '_blank');
        newWindow.document.write('<html><head><title>Comanda de Impressão</title>');
        newWindow.document.write('<style>body { font-family: monospace; font-size: 12px; margin: 0; padding: 10px; }</style>');
        newWindow.document.write('</head><body>');
        newWindow.document.write(printContent);
        newWindow.document.write('</body></html>');
        newWindow.document.close();
        newWindow.print();
    };

    // 6. NOVAS FUNÇÕES DE AÇÃO PARA OS PEDIDOS DE BALCÃO

    // Excluir Pedido
    window.deleteOrder = async (orderId) => {
        if (!confirm('Tem certeza que deseja excluir este pedido?')) {
            return;
        }

        try {
            const response = await fetch(`/caixa/excluir_pedido/${orderId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            });
            const result = await response.json();

            if (result.success) {
                alert('Pedido excluído com sucesso!');
                window.location.reload();
            } else {
                alert('Erro ao excluir pedido: ' + result.message);
            }
        } catch (error) {
            console.error('Erro ao excluir pedido:', error);
            alert('Ocorreu um erro ao excluir o pedido.');
        }
    };
    
    // Editar Pedido - LÓGICA REESCRITA
    const editCart = new Map();
    const editProductSearchInput = document.getElementById('edit-product-search');
    const editSearchResultsList = document.getElementById('edit-product-search-results');
    const editOrderItemsList = document.getElementById('edit-order-items-list');
    const editOrderTotalPriceSpan = document.getElementById('edit-order-total-price');
    const editOrderForm = document.getElementById('edit-order-form');

    const updateEditCartDisplay = () => {
        editOrderItemsList.innerHTML = '';
        let totalPrice = 0;
        editCart.forEach((item, productId) => {
            const listItem = document.createElement('li');
            listItem.className = 'flex justify-between items-start py-2 border-b last:border-b-0';
            listItem.innerHTML = `
                <div class="flex-1">
                    <div class="flex items-center">
                        <button type="button" class="text-danger hover:text-danger/70 mr-2" onclick="changeEditQuantity('${productId}', -1)">
                            <i data-lucide="minus-circle" class="w-5 h-5"></i>
                        </button>
                        <span class="font-bold text-lg">${item.quantity}</span>
                        <button type="button" class="text-success hover:text-success/70 ml-2" onclick="changeEditQuantity('${productId}', 1)">
                            <i data-lucide="plus-circle" class="w-5 h-5"></i>
                        </button>
                        <span class="ml-4 font-medium">${item.name}</span>
                    </div>
                    <textarea data-product-id="${productId}" class="mt-2 w-full text-sm p-1 border rounded" placeholder="Observação do item...">${item.notes || ''}</textarea>
                </div>
                <div class="text-right">
                    <span class="font-bold">R$ ${(item.quantity * item.price).toFixed(2)}</span>
                    <button type="button" class="ml-2 text-danger hover:text-danger/70" onclick="removeEditItem('${productId}')">
                        <i data-lucide="trash-2" class="w-4 h-4"></i>
                    </button>
                </div>
            `;
            editOrderItemsList.appendChild(listItem);
            totalPrice += item.quantity * item.price;
        });

        editOrderTotalPriceSpan.textContent = `R$ ${totalPrice.toFixed(2)}`;
        lucide.createIcons();
    };

    window.changeEditQuantity = (productId, change) => {
        const item = editCart.get(productId);
        if (item) {
            item.quantity += change;
            if (item.quantity <= 0) {
                editCart.delete(productId);
            }
            updateEditCartDisplay();
        }
    };

    window.removeEditItem = (productId) => {
        editCart.delete(productId);
        updateEditCartDisplay();
    };

    window.editOrder = async (orderId) => {
        try {
            const response = await fetch(`/caixa/editar_pedido/${orderId}`);
            const result = await response.json();

            if (result.success) {
                editCart.clear();
                result.order.items.forEach(item => {
                    editCart.set(String(item.product_id), {
                        name: item.name,
                        price: item.price,
                        quantity: item.quantity,
                        notes: item.notes
                    });
                });
                
                document.getElementById('edit-modal-order-id').textContent = orderId;
                document.getElementById('edit-order-id').value = orderId;
                document.getElementById('edit-notes').value = result.order.notes || '';
                
                updateEditCartDisplay();
                showModal('edit-order-modal');
            } else {
                alert('Erro ao carregar dados do pedido: ' + result.message);
            }
        } catch (error) {
            console.error('Erro ao carregar dados do pedido:', error);
            alert('Ocorreu um erro ao carregar os dados do pedido.');
        }
    };

    if (editProductSearchInput) {
        editProductSearchInput.addEventListener('input', async () => {
            const query = editProductSearchInput.value;
            if (query.length > 2) {
                const response = await fetch(`/caixa/buscar_produtos?q=${query}`);
                const products = await response.json();
                editSearchResultsList.innerHTML = '';
                if (products.length > 0) {
                    products.forEach(product => {
                        const li = document.createElement('li');
                        li.className = 'p-2 cursor-pointer hover:bg-gray-100 rounded';
                        li.textContent = `${product.name} (R$ ${product.price.toFixed(2)})`;
                        li.dataset.id = product.id;
                        li.dataset.name = product.name;
                        li.dataset.price = product.price;
                        editSearchResultsList.appendChild(li);
                    });
                    editSearchResultsList.classList.remove('hidden');
                } else {
                    editSearchResultsList.classList.add('hidden');
                }
            } else {
                editSearchResultsList.classList.add('hidden');
            }
        });
    }

    if (editSearchResultsList) {
        editSearchResultsList.addEventListener('click', (e) => {
            const li = e.target.closest('li');
            if (li) {
                const productId = li.dataset.id;
                const productName = li.dataset.name;
                const productPrice = parseFloat(li.dataset.price);

                if (editCart.has(productId)) {
                    const item = editCart.get(productId);
                    item.quantity += 1;
                } else {
                    editCart.set(productId, {
                        name: productName,
                        price: productPrice,
                        quantity: 1,
                        notes: ''
                    });
                }
                updateEditCartDisplay();
                editSearchResultsList.classList.add('hidden');
                editProductSearchInput.value = '';
            }
        });
    }

    if (editOrderItemsList) {
        editOrderItemsList.addEventListener('input', (e) => {
            if (e.target.tagName === 'TEXTAREA') {
                const productId = e.target.dataset.productId;
                if (editCart.has(productId)) {
                    editCart.get(productId).notes = e.target.value;
                }
            }
        });
    }

    if (editOrderForm) {
        editOrderForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const orderId = document.getElementById('edit-order-id').value;
            const newNotes = document.getElementById('edit-notes').value;
            
            if (editCart.size === 0) {
                alert('O pedido deve conter pelo menos um item.');
                return;
            }

            const items = Array.from(editCart).map(([productId, item]) => ({
                product_id: productId,
                quantity: item.quantity,
                notes: item.notes
            }));

            const data = {
                items,
                notes: newNotes
            };

            try {
                const response = await fetch(`/caixa/editar_pedido/${orderId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                
                if (result.success) {
                    alert('Pedido atualizado com sucesso!');
                    hideModal('edit-order-modal');
                    window.location.reload();
                } else {
                    alert('Erro ao atualizar pedido: ' + result.message);
                }
            } catch (error) {
                console.error('Erro ao atualizar pedido:', error);
                alert('Ocorreu um erro ao atualizar o pedido.');
            }
        });
    }

    // Imprimir Pedido
    window.printOrder = async (orderId) => {
        try {
            const response = await fetch(`/caixa/imprimir_pedido/${orderId}`);
            const result = await response.json();

            if (result.success) {
                displayReceiptModal(result.order_id, result.receipt_html);
            } else {
                alert('Erro ao gerar comanda de impressão: ' + result.message);
            }
        } catch (error) {
            console.error('Erro ao imprimir pedido:', error);
            alert('Ocorreu um erro ao imprimir o pedido.');
        }
    };

    // 7. INICIALIZAÇÃO
    lucide.createIcons();
    toggleChangeInput();
});