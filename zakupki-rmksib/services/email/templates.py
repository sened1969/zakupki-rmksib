"""Шаблоны email писем"""
from typing import Dict


def get_kp_request_template(
    product_name: str,
    specifications: str,
    company_data: Dict[str, str]
) -> str:
    """
    Генерирует HTML шаблон запроса коммерческого предложения
    
    Args:
        product_name: Название товара
        specifications: Технические требования
        company_data: Данные компании (manager_name, manager_position, phone, email)
    
    Returns:
        HTML строка письма
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            h2 {{
                color: #2c3e50;
            }}
            .product-info {{
                background-color: #f8f9fa;
                padding: 15px;
                border-left: 4px solid #007bff;
                margin: 20px 0;
            }}
            .requirements {{
                background-color: #fff;
                padding: 15px;
                border: 1px solid #dee2e6;
                margin: 20px 0;
            }}
            ol {{
                padding-left: 20px;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #dee2e6;
                font-size: 0.9em;
                color: #6c757d;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <p>Уважаемые коллеги!</p>
            
            <p>ООО «РМКСИБ» рассматривает возможность закупки и просит предоставить коммерческое предложение на поставку следующей продукции:</p>
            
            <div class="product-info">
                <p><strong>Наименование товара:</strong> {product_name}</p>
            </div>
            
            <div class="requirements">
                <p><strong>Технические требования:</strong></p>
                <p>{specifications.replace(chr(10), '<br>')}</p>
            </div>
            
            <p><strong>Требуемая информация:</strong></p>
            <ol>
                <li>Цена за единицу (с НДС и без НДС)</li>
                <li>Минимальная партия поставки</li>
                <li>Срок изготовления/поставки</li>
                <li>Условия оплаты</li>
                <li>Стоимость и условия доставки</li>
                <li>Наличие сертификатов соответствия</li>
                <li>Возможность производства под заказ</li>
                <li>Гарантийные обязательства</li>
            </ol>
            
            <p>Просим предоставить коммерческое предложение в течение <strong>3 рабочих дней</strong>.</p>
            
            <p><em>Данный запрос не является офертой.</em></p>
            
            <div class="footer">
                <p>С уважением,<br>
                {company_data.get('manager_name', 'Менеджер')}<br>
                {company_data.get('manager_position', 'Менеджер по закупкам')}<br>
                ООО «РМКСИБ»</p>
                
                <p>
                    Тел.: {company_data.get('phone', 'не указан')}<br>
                    Email: {company_data.get('email', 'не указан')}
                </p>
            </div>
        </div>
    </body>
    </html>
    """












