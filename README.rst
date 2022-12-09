========
Didiator
========

``didiator`` is an asynchronous library that implements the Mediator pattern and
uses the `DI <https://www.adriangb.com/di/>`_ library to help you to inject dependencies to called handlers

This library is inspired by the `MediatR <https://github.com/jbogard/MediatR>`_ used in C#
and follows CQRS principles

Installation
======

Didiator is available on pypi: https://pypi.org/project/didiator

.. code-block:: bash

    pip install -U didiator[di]

It will install ``didiator`` with its optional DI dependency that is necessary to use ``DiMiddleware`` and ``DiBuilder``

Examples
========

You can find examples in `this folder <https://github.com/SamWarden/didiator/tree/dev/examples>`_

Create Commands and Queries with handlers for them
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    @dataclass
    class CreateUser(Command[int]):
        user_id: int
        username: str

    class CreateUserHandler(CommandHandler[CreateUser, int]):
        def __init__(self, user_repo: UserRepo) -> None:
            self._user_repo = user_repo

        async def __call__(self, command: CreateUser) -> int:
            user = User(id=command.user_id, username=command.username)
            await self._user_repo.add_user(user)
            await self._user_repo.commit()
            return user.id

You can use functions as handlers

.. code-block:: python

    @dataclass
    class GetUserById(Query[User]):
        user_id: int

    async def handle_get_user_by_id(query: GetUserById, user_repo: UserRepo) -> User:
        user = await self._user_repo.get_user_by_id(user)
        return user

Create DiBuilder
~~~~~~~~~~~~~~~~

``DiBuilder`` is a facade for Container from DI with caching of `solving <https://www.adriangb.com/di/0.73.0/solving/>`_

``di_scopes`` is a sequence with the order of `scopes <https://www.adriangb.com/di/0.73.0/scopes/>`_

``di_builder.bind(...)`` will `bind <https://www.adriangb.com/di/0.73.0/binds/>`_ ``UserRepoImpl`` type to ``UserRepo`` protocol

.. code-block:: python

    di_scopes = ("request",)
    di_builder = DiBuilder(Container(), AsyncExecutor(), di_scopes)
    di_builder.bind(bind_by_type(Dependent(UserRepoImpl, scope="request"), UserRepo))

Create Mediator and register handlers to it
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create dispatchers with their middlewares and use them to initialize the ``MediatorImpl``

``cls_scope`` is a scope that will be used to bind class Command/Query handlers initialized during request handling

.. code-block:: python

    dispatchers_middlewares = (LoggingMiddleware(), DiMiddleware(di_builder, cls_scope="request"))
    command_dispatcher = CommandDispatcherImpl(middlewares=dispatchers_middlewares)
    query_dispatcher = QueryDispatcherImpl(middlewares=dispatchers_middlewares)

    mediator = MediatorImpl(command_dispatcher, query_dispatcher)

    # CreateUserHandler is not initialized during registration
    mediator.register_command_handler(CreateUser, CreateUserHandler)
    mediator.register_query_handler(GetUserById, handle_get_user_by_id)

Main usage
~~~~~~~~~~

Enter the ``"request"`` scope that was registered earlier and create a new Mediator with ``di_state`` bound

Use ``mediator.send(...)`` for commands and ``mediator.query(...)`` for queries

.. code-block:: python

        async with di_builder.enter_scope("request") as di_state:
            scoped_mediator = mediator.bind(di_state=di_state)

            # It will call CreateUserHandler(...).__call__(...) and inject UserRepoImpl to it
            user_id = await scoped_mediator.send(CreateUser(1, "Jon"))
            user = await scoped_mediator.query(GetUserById(user_id))
            print("User:",  user)
        # Session of UserRepoImpl will be closed after exiting the "request" scope

⚠️ **Attention: this is a beta version of** ``didiator`` **that depends on** ``DI``, **which is also in beta. Both of them can change their API!**

CQRS
====

CQRS stands for "`Command Query Responsibility Segregation <https://www.martinfowler.com/bliki/CQRS.html>`_".
Its idea about splitting the responsibility of commands (writing) and queries (reading) into different models.

``didiator`` have segregated ``.send(command)`` and ``.query(query)`` methods in its ``Mediator`` and
assumes that you will separate its handlers.
Use ``CommandMediator`` and ``QueryMediator`` protocols to explicitly define which method you need in ``YourController``

.. code-block:: mermaid

    graph LR;
        YourController-- Command -->Mediator;
        YourController-- Query -->Mediator;
        Mediator-. Command .->CommandDispatcher-.->di1[DiMiddleware]-.->CommandHandler;
        Mediator-. Query .->QueryDispatcher-.->di2[DiMiddleware]-.->QueryHandler;

``DiMiddleware`` initializes handlers and injects dependencies for them, you can just send a command with the data you need

Why ``didiator``?
=================

- Easy dependency injection to your business logic
- Separating dependencies from your controllers. They can just parse external requests and interact with the ``Mediator``
- CQRS
- Flexible configuration
- Middlewares support

Why not?
========

- You don't need it
- Maybe too low coupling: navigation becomes more difficult
- Didiator is in beta now
- No support for synchronous handlers

