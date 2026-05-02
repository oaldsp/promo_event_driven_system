# promo_event_driven_system
Este projeto consiste no desenvolvimento de um sistema distribuído baseado em microsserviços para gerenciamento e divulgação de promoções de produtos. A aplicação segue o modelo de arquitetura orientada a eventos (Event-Driven Architecture), utilizando o RabbitMQ como broker de mensagens para garantir comunicação indireta.

O sistema permite que usuários cadastrem promoções, votem em promoções existentes e recebam notificações conforme suas preferências. As promoções são processadas por diferentes microsserviços responsáveis por validação, ranqueamento e distribuição, sendo que promoções com alta popularidade são automaticamente classificadas como "hot deals".

Além disso, o sistema implementa mecanismos de segurança baseados em criptografia assimétrica.
