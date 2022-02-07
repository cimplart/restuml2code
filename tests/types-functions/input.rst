
:module: Det

Structural Design
*****************

Expected Interfaces
===================

.. uml::

    left to right direction

    component Det
    interface Dlt_Det

    Det ..> Dlt_Det: <<optional>>


Source File Description
=======================

.. table::
    :align: left

    +--------------+------------+-------------------------------------------+
    | File:        | Generated: |  Description:                             |
    +==============+============+===========================================+
    | Det.h        |    Yes     | Main Det module header.                   |
    +--------------+------------+-------------------------------------------+
    | Det_Types.h  |    Yes     | Type declarations for the Det module.     |
    +--------------+------------+-------------------------------------------+
    | Det.c        |    No      | Module implementation code.               |
    +--------------+------------+-------------------------------------------+
    | Det_MemMap.h |    No      | Module memory map.                        |
    +--------------+------------+-------------------------------------------+
    | SchM_Det.h   |    No      | Module synchronization.                   |
    +--------------+------------+-------------------------------------------+


Source File Dependencies
========================

.. uml::

    :restuml2code:

    @startuml

    left to right direction

    artifact Std_Types.h <<header>>
    artifact Det_Types.h <<header>>
    artifact Det.h <<header>>
    artifact Det.c <<source>>
    artifact Rte_Det.h <<header>>
    artifact Det_MemMap.h <<header>>
    artifact SchM_Det.h <<header>>

    Det.h ..> Std_Types.h : <<include>>
    Det.h ..> Det_Types.h : <<include>>
    Det.c ..> Det.h : <<include>>
    Det.c ..> Det_MemMap.h : <<include>>
    Det.c ..> SchM_Det.h : <<include>>
    Det.c ..> Rte_Det.h : <<include>>
    Det.h ..> Rte_Det.h : <<include>>
    @enduml

API Specification
*****************

Module Interface Types
======================

.. uml::

    allow_mixing
    left to right direction

    component Det

    class Det_ConfigType <<structure>> {
        int x
    }

    Det -- Det_ConfigType


Det_ReportCalloutType
---------------------

.. table::
    :align: left

    +--------------+----------------------------------------------------------------------------+
    | Type name:   | Det_ReportCalloutType                                                      |
    +==============+============================================================================+
    | Description: | Callout function type for reporting errors.                                |
    +--------------+----------------------------------------------------------------------------+
    | Kind:        | Typedef                                                                    |
    +--------------+----------------------------------------------------------------------------+
    | Declared in: | Det_Types.h                                                                |
    +--------------+----------------------------------------------------------------------------+
    | Type:        | .. code-block::                                                            |
    |              |                                                                            |
    |              |    Std_ReturnType (*Det_ReportCalloutType)(uint16, uint8, uint8, uint8)    |
    +--------------+----------------------------------------------------------------------------+


Det_ConfigType
--------------

.. table::
    :align: left

    +--------------+--------------------------------------------------------------------------------------------+
    | Type name:   | Det_ConfigType                                                                             |
    +==============+============================================================================================+
    | Description: | Configuration data structure of the Det module.                                            |
    +--------------+--------------------------------------------------------------------------------------------+
    | Kind:        | Structure                                                                                  |
    +--------------+------------------------+------------------+------------------------------------------------+
    | Declared in: | Det_Types.h                                                                                |
    +--------------+--------------------------------------------------------------------------------------------+
    | Elements:    | boolean                | forwardToDlt     | When true, the Det requires the Dlt interface  |
    |              |                        |                  | and forwards it's call to the function         |
    |              |                        |                  | Dlt_DetForwardErrorTrace.                      |
    |              +------------------------+------------------+----+-------------------------------------------+
    |              | Det_ReportCalloutType  | runtimeErrorCallout   | A callout function pointer for reporting  |
    |              |                        |                       | runtime errors.                           |
    |              +------------------------+-----------------------+-------------------------------------------+
    |              | Det_ReportCalloutType  | transientFaultCallout | A callout function pointer for reporting  |
    |              |                        |                       | transient faults.                         |
    +--------------+------------------------+-----------------------+-------------------------------------------+


Module Interface Functions
==========================

.. uml::

    left to right direction
    skinparam rectangle {
        BorderColor transparent
        FontColor transparent
        Shadowing false
    }

    component Det

    rectangle API {
        interface Det_Init
        interface Det_Start
        interface Det_ReportError
        interface Det_ReportRuntimeError
        interface Det_ReportTransientFault
        interface Det_GetVersionInfo
    }

    Det -r- Det_Init : <<realize>>
    Det -r- Det_Start : <<realize>>
    Det -r- Det_ReportError : <<realize>>
    Det -r- Det_ReportRuntimeError : <<realize>>
    Det -r- Det_ReportTransientFault : <<realize>>
    Det -r- Det_GetVersionInfo : <<realize>>

    Det --[hidden]-- API


Det_Init
--------

.. table::
    :align: left

    +--------------------------+------------------------------------------------------------+
    | Function name:           | Det_Init                                                   |
    +==========================+============================================================+
    | Description:             | Service to initialize the Default Error Tracer.            |
    +--------------------------+------------------------------------------------------------+
    | Syntax:                  | .. code-block::                                            |
    |                          |                                                            |
    |                          |     void Det_Init(                                         |
    |                          |         const Det_ConfigType* ConfigPtr                    |
    |                          |         )                                                  |
    +--------------------------+------------------------------------------------------------+
    | Declared in:             | Det.h                                                      |
    +--------------------------+------------------------------------------------------------+
    | May be called from ISR:  | No                                                         |
    +--------------------------+------------------------------------------------------------+
    | Reentrancy:              | Non-Reentrant                                              |
    +--------------------------+------------------------------------------------------------+
    | Return value:            | None                                                       |
    +--------------------------+------------+-----------------------------------------------+
    | Parameters [in]:         | ConfigPtr  | Pointer to the chosen configuration set.      |
    +--------------------------+------------+-----------------------------------------------+


Det_ReportError
---------------

.. table::
    :align: left

    +--------------------------+------------------------------------------------------------+
    | Function name:           | Det_ReportError                                            |
    +==========================+============================================================+
    | Description:             | Service to report development errors.                      |
    +--------------------------+------------------------------------------------------------+
    | Syntax:                  | .. code-block::                                            |
    |                          |                                                            |
    |                          |   Std_ReturnType Det_ReportError(                          |
    |                          |       uint16 ModuleId,                                     |
    |                          |       uint8 InstanceId,                                    |
    |                          |       uint8 ApiId,                                         |
    |                          |       uint8 ErrorId                                        |
    |                          |       )                                                    |
    +--------------------------+------------------------------------------------------------+
    | Declared in:             | Det.h                                                      |
    +--------------------------+------------------------------------------------------------+
    | May be called from ISR:  | Yes                                                        |
    +--------------------------+------------------------------------------------------------+
    | Reentrancy:              | Reentrant                                                  |
    +--------------------------+------------------+-----------------------------------------+
    | Return value:            | Std_ReturnType   | Never returns a value, but has a return |
    |                          |                  | type for compatibility with services    |
    |                          |                  | and hooks.                              |
    +--------------------------+------------+-----+-----------------------------------------+
    | Parameters [in]:         | ModuleId   | Module ID of calling module.                  |
    |                          +------------+-----------------------------------------------+
    |                          | InstanceId | The identifier of the index based instance    |
    |                          |            | of a module, starting from 0, if the          |
    |                          |            | module is a single instance module it         |
    |                          |            | shall pass 0 as the InstanceId.               |
    |                          +------------+-----------------------------------------------+
    |                          | ApiId      | ID of API service in which error is detected  |
    |                          |            | (defined in SWS of calling module)            |
    |                          +------------+-----------------------------------------------+
    |                          | ErrorId    | ID of detected development error              |
    |                          |            | (defined in SWS of calling module)            |
    +--------------------------+------------+-----------------------------------------------+

